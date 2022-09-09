import math


class Planner:
    def __init__(self):
        self.game = None
        self.data = None
        self.static_data = None
        self.player_id = None
        self.mothership_coords = None

    def update_game(self, game):
        self.game = game
        self.data = self.game.data
        self.static_data = self.game.static_data
        self.player_id = self.game.player_id

    def get_my_ships(self):
        return {ship_id: ship for ship_id, ship in
                self.data.ships.items() if ship.player == self.player_id}

    def get_mothership_coords(self):
        if self.mothership_coords:
            return self.mothership_coords
        my_mothership = None
        for ship in self.data.ships.values():
            if ship.player == self.player_id and ship.ship_class == '1':
                my_mothership = ship
        if not my_mothership:
            for ship in self.data.wrecks.values():
                if ship.player == self.player_id and ship.ship_class == '1':
                    my_mothership = ship
        self.mothership_coords = my_mothership.position
        return self.mothership_coord

    @staticmethod
    def dist(coords1, coords2):
        return math.sqrt((coords1[0] - coords2[0]) ** 2 + (coords1[1] - coords2[1]) ** 2)
