import math
import random
import datetime
import traceback
import enum
import yaml
import sys
from collections import defaultdict
from collections import Counter
from pprint import pprint
from typing import Dict, Optional, List
from dataclasses import dataclass

from space_tycoon_client import ApiClient
from space_tycoon_client import Configuration
from space_tycoon_client import GameApi
from space_tycoon_client.models.credentials import Credentials
from space_tycoon_client.models.current_tick import CurrentTick
from space_tycoon_client.models.data import Data
from space_tycoon_client.models.destination import Destination
from space_tycoon_client.models.end_turn import EndTurn
from space_tycoon_client.models.stop_command import StopCommand
from space_tycoon_client.models.player import Player
from space_tycoon_client.models.player_id import PlayerId
from space_tycoon_client.models.ship import Ship
from space_tycoon_client.models.static_data import StaticData
from space_tycoon_client.rest import ApiException
from cargo_planner import CargoPlanner
from fighter_planner import FighterPlanner
from mothership_planner import MothershipPlanner

CONFIG_FILE = "config.yml"


class ConfigException(Exception):
    pass


@dataclass
class Coords:
    x: int
    y: int

    def from_position(pos: List[int]) -> 'Coords':
        return Coords(
            x=pos[0],
            y=pos[1]
        )


@dataclass
class EnemyShip:
    id: str
    ship_class: str
    position: Coords
    vector: Coords
    distance: float
    ticks_approaching: int
    target_ship_id: int

    def __str__(self):
        return f'{self.ship_class}:{self.id}'


ships_class_mapping={
    '1': 'mothership',
    '2': 'hauler',
    '3': 'shipper',
    '4': 'fighter',
    '5': 'bomber',
    '6': 'destroyer',
    '7': 'shipyard'
}

def ship_class_id_to_human(id: str) -> str:
    return ships_class_mapping[id]

SUSPICIOUS_TICK_INCOMING=15
SUSPICIOUS_DISTANCE=170


attacking_ship_classes={'mothership', 'fighter', 'bomber', 'desctroyer'}

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

        self.enemies_ships: List[EnemyShip] = []
        self.my_ships: List[Ship] = []

        # this part is custom logic, feel free to edit / delete
        if self.player_id not in self.data.players:
            raise Exception("Logged as non-existent player")
        self.recreate_me()
        print(f"playing as [{self.me.name}] id: {self.player_id}")
        self.cargo_planner = CargoPlanner()
        self.fighter_planner = FighterPlanner()
        self.mothership_planner = MothershipPlanner()

    def recreate_me(self):
        self.me: Player = self.data.players[self.player_id]

    def update_planners(self):
        self.cargo_planner.update_game(self)
        self.fighter_planner.update_game(self)
        self.mothership_planner.update_game(self)

    def game_loop(self):
        while True:
            print("-" * 30)
            try:
                print(f"tick {self.tick} season {self.season}")
                self.data: Data = self.client.data_get()
                if self.data.player_id is None:
                    raise Exception("I am not correctly logged in. Bailing out")

                t0 = datetime.datetime.now()
                try:
                    self.update_planners()
                    self.game_logic()
                finally:
                    print(f'Tick took: {datetime.datetime.now() - t0}')

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
                traceback.print_exc()

<<<<<<< variant A
>>>>>>> variant B
    def get_cargo_plan(self):
        mothership_coords = self.get_mothership_coords()
        buys = defaultdict(list)
        sells = defaultdict(list)
        for planet, planet_data in self.data.planets.items():
            for resource, resource_data in planet_data.resources.items():
                if resource_data.buy_price is not None:
                    buys[resource].append({'planet': planet,
                                           'amount': resource_data.amount,
                                           'buy_price': resource_data.buy_price,
                                           'position': planet_data.position})
                if resource_data.sell_price is not None:
                    sells[resource].append({'planet': planet,
                                            'sell_price': resource_data.sell_price,
                                            'position': planet_data.position})
        resources = sells.keys() & buys.keys()
        best_deals = []
        for resource in resources:
            for buy in buys[resource]:
                for sell in sells[resource]:
                    price = sell['sell_price'] - buy['buy_price']
                    d = self.dist(mothership_coords, buy['position']) + self.dist(buy['position'], sell['position'])
                    score = price / (d ** 1.3)
                    best_deals.append((score, resource, buy, sell))
        return sorted(best_deals, reverse=True, key=lambda tup: tup[0])

    def get_cargo_command(self, ship, plan):
        if ship.resources.keys():
            resource = list(ship.resources.keys())[0]
            # score, resource, buy, sell
            for i, p in enumerate(plan):
                if p[1] == resource:
                    planet = p[3]['planet']
                    amount = ship.resources[resource]['amount']
                    return TradeCommand(target=planet, resource=resource, amount=-amount)

        score, resource, buy, sell = plan.pop(0)
        # ship_load = sum(r['amount'] for r in ship.resources.values())
        # ship_free_capacity = ship.cargo_capacity - ship_load # todo must use common data

        return TradeCommand(target=buy['planet'], resource=resource, amount=min(10 if ship.ship_class == '3' else 40,
                                                                                buy['amount']))

    @staticmethod
    def move_vector(ship: Ship) -> Coords:
        return Coords(x=ship.prev_position[0] - ship.position[0],
                      y=ship.prev_position[1] - ship.position[1])

    def dist(self, coords1, coords2):
        return math.sqrt((coords1[0] - coords2[0]) ** 2 + (coords1[1] - coords2[1]) ** 2)

    def construct_ship(self, ship_class):
        my_money = self.data.players[self.player_id].net_worth.money
        ship_price = self.static_data.ship_classes[ship_class].price
        if (my_money - ship_price) > 80000:
            return ConstructCommand(ship_class=ship_class)

    def get_mothership_coords(self):
        my_mothership = None
        for ship in self.data.ships.values():
            if ship.player == self.player_id and ship.ship_class == '1':
                my_mothership = ship
        if not my_mothership:
            for ship in self.data.wrecks.values():
                if ship.player == self.player_id and ship.ship_class == '1':
                    my_mothership = ship
        return my_mothership.position

    def get_mothership_command(self, ship, ship_id):
        # return MoveCommand(destination=Destination(coordinates=[-412, -670]))
        # return AttackCommand(target='162900')
        if self.data.ships[ship_id].life < 800:
            return RepairCommand()
        my_ships: Dict[Ship] = {ship_id: ship for ship_id, ship in
                                self.data.ships.items() if ship.player == self.player_id}
        ship_type_cnt = Counter(self.static_data.ship_classes[ship.ship_class].name for ship in my_ships.values())

        if 'fighter' not in ship_type_cnt or ship_type_cnt['fighter'] < 3:
            return self.construct_ship(ship_class='4')

        other_fighter_ships = {ship_id: ship for ship_id, ship in self.data.ships.items() if
                               ship.player != self.player_id and ship.ship_class in ('1', '4', '5', '6')}
        my_coords = self.data.ships[ship_id].position
        other_coords = {ship_id: self.data.ships[ship_id].position for ship_id in other_fighter_ships}
        distances = Counter(
            {ship_id: self.dist(my_coords, other_coord) for ship_id, other_coord in other_coords.items()})
        distances = [(self.data.ships[ship_id].ship_class, ship_id, dist)
                     for ship_id, dist in distances.items() if dist < 100]
        distances = sorted(distances, reverse=True)
        if distances:
            _, ship_id, d = distances[0]
            return AttackCommand(target=ship_id)

        return self.construct_ship(ship_class='2')

    def get_fighter_command(self, ship, ship_id):
        # other_motherships = {ship_id: ship for ship_id, ship in
        #                      self.data.ships.items() if ship.player != self.player_id and ship.ship_class == '1'}
        # if other_motherships:
        #     mothership_id = list(other_motherships.keys())[0]
        #     return AttackCommand(target=mothership_id)

        other_ships = {ship_id: ship for ship_id, ship in self.data.ships.items() if ship.player != self.player_id}
        my_coords = self.data.ships[ship_id].position
        other_coords = {ship_id: self.data.ships[ship_id].position for ship_id in other_ships}
        distances = Counter(
            {ship_id: self.dist(my_coords, other_coord) for ship_id, other_coord in other_coords.items()})
        distances = [(self.data.ships[ship_id].ship_class, ship_id, dist)
                     for ship_id, dist in distances.items() if dist < 5]
        distances = sorted(distances, reverse=True)
        if distances:
            _, ship_id, d = distances[0]
            return AttackCommand(target=ship_id)

        mothership_coords = self.get_mothership_coords()
        return MoveCommand(destination=Destination(coordinates=mothership_coords))

    def ship_stuck(self, ship, ship_id):
        if ship.command and ship.command.type == 'trade':
            planet_id = ship.command.target
            planet = self.data.planets[planet_id]
            return planet.position == ship.position

    def detect_enemies(self):
        '''saves positions and vector of enemy ships into self.enemies_ships'''
        self.enemies_ships = []
        for ship_id, ship in self.data.ships.items():
            if ship_class_id_to_human(ship.ship_class) in attacking_ship_classes and ship.player != self.player_id:
                self.enemies_ships.append(EnemyShip(
                    id=ship_id,
                    position=Coords.from_position(ship.position),
                    vector=self.move_vector(ship)
                ))

    def update_incoming_enemies(self):
        '''checks which ships are probably targeted by enemies'''
        for enemy_ship in self.enemies_ships:
            target = min(
                [(self.dist(s, enemy_ship), s) for s self.own_ships
                 if self.vector_points_to_point(enemy_ship.position, enemy_ship.vector, s)],
                key=lambda x: x[0])
            if target[0] < enemy_ship.distance
                enemy_ship.ticks_approaching += 1
                enemy_ship.distance = target[0]

            if enemy_ship.ticks_approaching >= SUSPICIOUS_TICK_INCOMING or \
               enemy_ship.distance <= SUSPICIOUS_DISTANCE:
                enemy_ship.target_ship_id = target[1].id
                print(f'detected ship: {enemy_ship} targeting our ship: {target[1]}')

    def get_my_ships(self):
        self.my_ships = {ship_id: ship for ship_id, ship in
                         self.data.ships.items() if ship.player == self.player_id}

    @staticmethod
    def vector_points_to_point(p0: Coords, vec: Coords, target: Coords) -> bool:
        par0, par1 = (target.x - p0.x) / coords.x, (target.y - p0.y) / coords.y
        return abs(par0 - par1) < 0.1

======= end
    def game_logic(self):
        self.recreate_me()
        my_ships = self.mothership_planner.get_my_ships()

        ship_type_cnt = Counter(
            (self.static_data.ship_classes[ship.ship_class].name for ship in my_ships.values()))
        pretty_ship_type_cnt = ', '.join(
            f"{k}:{v}" for k, v in ship_type_cnt.most_common())
        print(f"I have {len(my_ships)} ships ({pretty_ship_type_cnt})")

        plan = self.cargo_planner.get_cargo_plan()

        commands = {}
        for ship_id, ship in my_ships.items():
            command = None
            if ship.ship_class in ('2', '3'):
                command = self.cargo_planner.plan(ship, ship_id, plan)
            if ship.ship_class == '1':
                command = self.mothership_planner.plan(ship, ship_id)
            if ship.ship_class in ('4', '5', '6'):
                command = self.fighter_planner.plan(ship, ship_id)
            if command:
                commands[ship_id] = command

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
        except KeyboardInterrupt:
            sys.exit(0)
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
