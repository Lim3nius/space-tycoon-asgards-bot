from collections import Counter

from planner import Planner
from space_tycoon_client.models.construct_command import ConstructCommand
from space_tycoon_client.models.repair_command import RepairCommand
from space_tycoon_client.models.attack_command import AttackCommand
from space_tycoon_client.models.stop_command import StopCommand
from space_tycoon_client.models.move_command import MoveCommand
from space_tycoon_client.models.destination import Destination


class MothershipPlanner(Planner):
    def __init__(self):
        super().__init__()

    def construct_ship(self, ship_class):
        my_money = self.data.players[self.player_id].net_worth.money
        ship_price = self.static_data.ship_classes[ship_class].price
        if (my_money - ship_price) > 1000000:
            return ConstructCommand(ship_class=ship_class)

    def plan(self, ship, ship_id):
        # return AttackCommand(target='1552944')
        # return StopCommand()
        return MoveCommand(destination=Destination(coordinates=[1033,-638]))
        # return AttackCommand(target='12716')
        if self.data.ships[ship_id].life < 600:
            return RepairCommand()
        my_ships = {ship_id: s for ship_id, s in self.data.ships.items() if s.player == self.player_id}
        ship_type_cnt = Counter(self.static_data.ship_classes[s.ship_class].name for s in my_ships.values())
        # if 'fighter' not in ship_type_cnt or ship_type_cnt['fighter'] < 1 and self.game.tick < 2:
        #     command = self.construct_ship(ship_class='4')
        #     if command:
        #         return command
        other_fighter_ships = {ship_id: s for ship_id, s in self.data.ships.items() if
                               s.player != self.player_id and s.ship_class in ('1', '4', '5', '6')}
        other_fighter_ship_type_cnt = Counter(self.static_data.ship_classes[s.ship_class].name
                                              for s in other_fighter_ships.values())
        my_coords = self.data.ships[ship_id].position
        other_coords = {ship_id: self.data.ships[ship_id].position for ship_id in other_fighter_ships}
        distances = Counter(
            {ship_id: self.dist(my_coords, other_coord) for ship_id, other_coord in other_coords.items()})

        distances = [(self.data.ships[ship_id].ship_class, ship_id, self.data.ships[ship_id].player, dist)
                     for ship_id, dist in distances.items()]
        distances = sorted(distances, reverse=True)
        print('distances', distances)
        if distances:
            close_fighters = [(c, sid, p, d) for c, sid, p, d in distances if c == '4' and d < 5]
            if close_fighters:
                c, sid, p, d = close_fighters[0]
                return AttackCommand(target=sid)
            close_ms = [(c, sid, p, d) for c, sid, p, d in distances if c == '1' and d < 3]
            if close_ms:
                c, sid, p, d = close_ms[0]
                return AttackCommand(target=sid)
            duck_ms = [(c, sid, p, d) for c, sid, p, d in distances if c == '1' and p == '5']
            # duck_ms = [(c, sid, p, d) for c, sid, p, d in distances if c == '1' and p in ('1', '3')]  # TODO local test
            if duck_ms:
                c, sid, p, d = duck_ms[0]
                return AttackCommand(target=sid)
            other_cargo = [(c, sid, p, d) for c, sid, p, d in distances if c in ('2', '3') and d < 3]
            if other_cargo:
                c, sid, p, d = other_cargo[0]
                return AttackCommand(target=sid)
        if self.game.tick > 1000:
            # if 'hauler' not in ship_type_cnt or ship_type_cnt['hauler'] < 3:
            #     command = self.construct_ship(ship_class='2')
            #     if command:
            #         return command
            if 'fighter' not in other_fighter_ship_type_cnt:
                if 'fighter' not in ship_type_cnt or ship_type_cnt['fighter'] < 3:
                    command = self.construct_ship(ship_class='4')
                    if command:
                        return command
            return self.construct_ship(ship_class='2')
