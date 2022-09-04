import random
import traceback
from collections import defaultdict
from collections import Counter
from pprint import pprint
from typing import Dict
from typing import Optional

import yaml
from space_tycoon_client import ApiClient
from space_tycoon_client import Configuration
from space_tycoon_client import GameApi
from space_tycoon_client.models.credentials import Credentials
from space_tycoon_client.models.current_tick import CurrentTick
from space_tycoon_client.models.data import Data
from space_tycoon_client.models.destination import Destination
from space_tycoon_client.models.end_turn import EndTurn
from space_tycoon_client.models.move_command import MoveCommand
from space_tycoon_client.models.trade_command import TradeCommand
from space_tycoon_client.models.player import Player
from space_tycoon_client.models.player_id import PlayerId
from space_tycoon_client.models.ship import Ship
from space_tycoon_client.models.static_data import StaticData
from space_tycoon_client.rest import ApiException

CONFIG_FILE = "config.yml"


class ConfigException(Exception):
    pass


class Game:
    def __init__(self, api_client: GameApi, config: Dict[str, str]):
        self.me: Optional[Player] = None
        self.config = config
        self.client = api_client
        self.player_id = self.login()
        self.static_data: StaticData = self.client.static_data_get()
        self.data: Data = self.client.data_get()
        self.season = self.data.current_tick.season
        self.tick = self.data.current_tick.tick
        # this part is custom logic, feel free to edit / delete
        if self.player_id not in self.data.players:
            raise Exception("Logged as non-existent player")
        self.recreate_me()
        print(f"playing as [{self.me.name}] id: {self.player_id}")

    def recreate_me(self):
        self.me: Player = self.data.players[self.player_id]

    def game_loop(self):
        while True:
            print("-" * 30)
            try:
                print(f"tick {self.tick} season {self.season}")
                self.data: Data = self.client.data_get()
                if self.data.player_id is None:
                    raise Exception("I am not correctly logged in. Bailing out")
                self.game_logic()
                current_tick: CurrentTick = self.client.end_turn_post(EndTurn(
                    tick=self.tick,
                    season=self.season
                ))
                self.tick = current_tick.tick
                self.season = current_tick.season
            except ApiException as e:
                if e.status == 403:
                    print(f"New season started or login expired: {e}")
                    break
                else:
                    raise e
            except Exception as e:
                print(f"!!! EXCEPTION !!! Game logic error {e}")
                traceback.print_exception(e)

    def game_logic(self):
        # todo throw all this away
        self.recreate_me()
        my_ships: Dict[Ship] = {ship_id: ship for ship_id, ship in
                                self.data.ships.items() if ship.player == self.player_id}
        ship_type_cnt = Counter(
            (self.static_data.ship_classes[ship.ship_class].name for ship in my_ships.values()))
        pretty_ship_type_cnt = ', '.join(
            f"{k}:{v}" for k, v in ship_type_cnt.most_common())
        print(f"I have {len(my_ships)} ships ({pretty_ship_type_cnt})")

        sells = defaultdict(dict)
        buys = defaultdict(dict)

        for planet, planet_data in self.data.planets.items():
            for resource, resource_data in planet_data.resources.items():
                if resource_data.buy_price is not None:
                    buys[resource][planet] = resource_data
                if resource_data.sell_price is not None:
                    sells[resource][planet] = resource_data

        resources = sells.keys() & buys.keys()

        best_buys = dict()
        for resource in resources:
            best_buy_price = float('inf')
            best_buy_planet = None
            for planet, resource_data in buys[resource].items():
                if resource_data.buy_price < best_buy_price:
                    best_buy_price = resource_data.buy_price
                    best_buy_planet = planet
            best_buys[resource] = {'planet': best_buy_planet, 'buy_price': best_buy_price}

        best_sells = dict()
        for resource in resources:
            best_sell_price = float('inf')
            best_sell_planet = None
            for planet, resource_data in sells[resource].items():
                if resource_data.sell_price < best_sell_price:
                    best_sell_price = resource_data.sell_price
                    best_sell_planet = planet
            best_sells[resource] = {'planet': best_sell_planet, 'sell_price': best_sell_price}

        best_deals = Counter({r: best_sells[r]['sell_price'] - best_buys[r]['buy_price'] for r in resources})
        plan = []
        for resource, profit in best_deals.most_common():
            planet = best_buys[resource]['planet']
            amount = buys[resource][planet].amount
            plan.append((resource, planet, amount))

        commands = {}
        for ship_id, ship in my_ships.items():
            if ship.ship_class != '3':
                continue
            if ship.command is not None:
                continue
            if ship.resources.keys():
                resource = list(ship.resources.keys())[0]
                planet = best_sells[resource]['planet']
                amount = ship.resources[resource]['amount']
                if amount:
                    commands[ship_id] = TradeCommand(target=planet, resource=resource, amount=-amount)
                    continue
            random_planet_id = random.choice(list(self.data.planets.keys()))
            print(f"sending {ship_id} to {self.data.planets[random_planet_id].name}({random_planet_id})")
            # commands[ship_id] = MoveCommand(type="move", destination=Destination(target=random_planet_id))
            resource, planet, amount = plan.pop(0)
            ship_load = sum(r['amount'] for r in ship.resources.values())
            # ship_free_capacity = ship.cargo_capacity - ship_load # todo must use common data
            commands[ship_id] = TradeCommand(target=planet, resource=resource, amount=min(amount, 10))

        if commands:
            print('Commands:')
            pprint(commands)
        try:
            self.client.commands_post(commands)
        except ApiException as e:
            if e.status == 400:
                print("some commands failed")
                print(e.body)

    def login(self) -> str:
        if self.config["user"] == "?":
            raise ConfigException
        if self.config["password"] == "?":
            raise ConfigException
        player, status, headers = self.client.login_post_with_http_info(Credentials(
            username=self.config["user"],
            password=self.config["password"],
        ), _return_http_data_only=False)
        self.client.api_client.cookie = headers['Set-Cookie']
        player: PlayerId = player
        return player.id


def main_loop(api_client, config):
    game_api = GameApi(api_client=api_client)
    while True:
        try:
            game = Game(game_api, config)
            game.game_loop()
            print("season ended")
        except ConfigException as e:
            print(f"User / password was not configured in the config file [{CONFIG_FILE}]")
            return
        except Exception as e:
            print(f"Unexpected error {e}")


def main():
    config = yaml.safe_load(open(CONFIG_FILE))
    print(f"Loaded config file {CONFIG_FILE}")
    print(f"Loaded config values {config}")
    configuration = Configuration()
    if config["host"] == "?":
        print(f"Host was not configured in the config file [{CONFIG_FILE}]")
        return

    configuration.host = config["host"]

    main_loop(ApiClient(configuration=configuration, cookie="SESSION_ID=1"), config)


if __name__ == '__main__':
    main()
