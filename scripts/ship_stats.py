#!/usr/bin/env python3

import requests
import json
from dataclasses import dataclass, field

ships_class_mapping={
    '1': 'mothership',
    '2': 'hauler',
    '3': 'shipper',
    '4': 'fighter',
    '5': 'bomber',
    '6': 'destroyer',
    '7': 'shipyard'
}

url = 'https://space-tycoon.garage-trip.cz/data'

@dataclass
class ShipStats:
    mothership: int = 0
    hauler: int = 0
    shipper: int = 0
    fighter: int = 0
    bomber: int = 0
    destroyer: int = 0
    shipyard: int = 0

    def __getitem__(self, key: str):
        return self.__dict__[key]

    def __setitem__(self, key: str, val):
        self.__dict__[key] = val

@dataclass
class Player:
    name: str
    ships: ShipStats = field(default_factory=ShipStats)


if __name__ == '__main__':
    res = requests.get(url)
    if res.status_code != 200:
        print(f'failed with code: {res.status_code}, {res.text}')

    data = json.loads(res.text)
    player_map = {k: Player(name=v['name']) for k, v in data['players'].items()}

    for ship in data['ships'].values():
        cls_name = ships_class_mapping[ship['shipClass']]
        s = player_map[ship['player']].ships
        s[cls_name] += 1

    print('team' + ' ' * 16 + '| mot | hau | shp | fig | bmb | des | syd |')
    for p in player_map.values():
        print(f'{p.name: <20}', end='')
        for c in ships_class_mapping.values():
            print(f'|{p.ships[c]: >5}', end='')
        print('|')
