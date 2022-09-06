import math
import random
import datetime
import traceback
import enum
import yaml
import sys
import argparse
from collections import defaultdict
from collections import Counter
from pprint import pprint
from typing import Dict, Optional, List
from dataclasses import dataclass

import numpy as np
from math import cos, sin

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
            x=float(pos[0]),
            y=float(pos[1])
        )


@dataclass
class EnemyShip:
    id: str
    ship_class: str
    position: Coords
    vector: Coords = Coords(0,0)
    distance: float = 0
    ticks_approaching: int = 0
    target_ship_id: int = 0

    def __str__(self):
        return f'{self.ship_class}:{self.id}'

    def __hash__(self):
        return self.id

def rotate_vector(vec: Coords, angle: int) -> Coords:
    alpha = np.deg2rad(angle)
    rot = np.array([[cos(alpha), -sin(alpha)],
                    [sin(alpha), cos(alpha)]])

    new_vec = np.dot(rot, np.array([vec.x, vec.y]))
    return Coords(x=int(new_vec[0]), y=int(new_vec[1]))

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
SHIP_ANGLE=10  # angle to consider to both sides from inital to result


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

        self.enemies_ships: Set[EnemyShip] = []
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

    @staticmethod
    def move_vector(ship: Ship) -> Coords:
        return Coords(x=ship.prev_position[0] - ship.position[0],
                      y=ship.prev_position[1] - ship.position[1])

    def detect_enemies(self):
        '''saves positions and vector of enemy ships into self.enemies_ships'''
        self.enemies_ships = {}
        for ship_id, ship in self.data.ships.items():
            ship_class = ship_class_id_to_human(ship.ship_class)
            if ship_class in attacking_ship_classes and ship.player != self.player_id:
                self.enemies_ships.update([EnemyShip(
                    id=ship_id,
                    ship_class=ship_class,
                    position=Coords.from_position(ship.position),
                    vector=self.move_vector(ship)
                )])

        print(f'detected enemies: {self.enemies_ships}')

    def update_incoming_enemies(self):
        '''checks which ships are probably targeted by enemies'''
        for enemy_ship in self.enemies_ships:
            # breakpoint()
            comp = [(self.dist(s.position, enemy_ship.position), s) for s in self.my_ships.values()
                    if self.vector_points_to_point(enemy_ship.position, enemy_ship.vector, Coords.from_position(s.position))]
            if not comp:
                return

            target = min( comp,
                key=lambda x: x[0])
            if target[0] < enemy_ship.distance:
                enemy_ship.ticks_approaching += 1
                enemy_ship.distance = target[0]

            if enemy_ship.ticks_approaching >= SUSPICIOUS_TICK_INCOMING or \
               enemy_ship.distance <= SUSPICIOUS_DISTANCE:
                enemy_ship.target_ship_id = target[1].id
                print(f'detected ship: {enemy_ship} targeting our ship: {target[1]}')


    @staticmethod
    def point_heading_for_point(point: Coords, vector: Coords, target: Coords) -> bool:
        if vec.x == 0 and vec.y ==0:
            return point == target

        vec0 = rotate_vector(vector, SHIP_ANGLE)
        vec1 = rotate_vector(vector, -SHIP_ANGLE)



    @staticmethod
    def vector_points_to_point(point: Coords, vec: Coords, target: Coords) -> bool:
        if vec.x == 0 and vec.y ==0:
            return point == target

        if vec.y == 0:
            return (target.x - point.x) / vec.x != 0

        if vec.x == 0:
            return (target.y - point.y) / vec.y != 0

        par0 = (target.x - point.x) / vec.x
        par1 = (target.y - point.y) / vec.y
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
    a = argparse.ArgumentParser()
    a.add_argument('-c', '--config', default=CONFIG_FILE, help='Option to specify alternative config')
    args = a.parse_args()

    config = yaml.safe_load(open(args.config))
    print(f"Loaded config file {args.config}")
    print(f"Loaded config values {config}")
    configuration = Configuration()
    if config["host"] == "?":
        print(f"Host was not configured in the config file [{args.config}]")
        return

    configuration.host = config["host"]

    main_loop(ApiClient(configuration=configuration, cookie="SESSION_ID=1"), config)


if __name__ == '__main__':
    main()
