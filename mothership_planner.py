from collections import Counter

from planner import Planner
from space_tycoon_client.models.construct_command import ConstructCommand
from space_tycoon_client.models.repair_command import RepairCommand
from space_tycoon_client.models.attack_command import AttackCommand


class MothershipPlanner(Planner):
    def __init__(self):
        super().__init__()

    def construct_ship(self, ship_class):
        my_money = self.data.players[self.player_id].net_worth.money
        ship_price = self.static_data.ship_classes[ship_class].price
        if (my_money - ship_price) > 80000:
            return ConstructCommand(ship_class=ship_class)

    def plan(self, ship, ship_id):
        # return MoveCommand(destination=Destination(coordinates=[-412, -670]))
        # return AttackCommand(target='230989')
        if self.data.ships[ship_id].life < 600:
            return RepairCommand()
        my_ships = {ship_id: ship for ship_id, ship in
                    self.data.ships.items() if ship.player == self.player_id}
        ship_type_cnt = Counter(self.static_data.ship_classes[ship.ship_class].name for ship in my_ships.values())

        if 'fighter' not in ship_type_cnt or ship_type_cnt['fighter'] < 1:
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
        if self.game.tick > 800:
            return self.construct_ship(ship_class='2')
