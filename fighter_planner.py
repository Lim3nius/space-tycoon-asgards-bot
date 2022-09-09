from collections import Counter

from planner import Planner
from space_tycoon_client.models.move_command import MoveCommand
from space_tycoon_client.models.attack_command import AttackCommand
from space_tycoon_client.models.destination import Destination
from space_tycoon_client.models.repair_command import RepairCommand


class FighterPlanner(Planner):
    def __init__(self):
        super().__init__()

    def plan(self, ship, ship_id):
        if self.data.ships[ship_id].life < 50:
            return RepairCommand()
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
                     for ship_id, dist in distances.items()
                     if self.data.ships[ship_id].ship_class == '4']
        distances = sorted(distances, reverse=True)
        if distances:
            _, ship_id, d = distances[0]
            return AttackCommand(target=ship_id)

        distances = Counter(
            {ship_id: self.dist(my_coords, other_coord) for ship_id, other_coord in other_coords.items()})
        distances = [(self.data.ships[ship_id].ship_class, ship_id, dist)
                     for ship_id, dist in distances.items()
                     if dist < 1500 and self.data.ships[ship_id].ship_class in ('2', '3') and
                     ('amazon' in self.data.ships[ship_id].name or 'ducks' in self.data.ships[ship_id].name or
                      'opponent' in self.data.ships[ship_id].name)]
        distances = sorted(distances, reverse=True)
        if distances:
            _, ship_id, d = distances[0]
            return AttackCommand(target=ship_id)

        mothership_coords = self.get_mothership_coords()
        return MoveCommand(destination=Destination(coordinates=mothership_coords))
