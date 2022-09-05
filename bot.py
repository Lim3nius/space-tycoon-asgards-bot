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
    position: Coords
    vector: Coords


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
