from collections import Counter
from collections import defaultdict

from planner import Planner
from space_tycoon_client.models.trade_command import TradeCommand
from space_tycoon_client.models.move_command import MoveCommand
from space_tycoon_client.models.destination import Destination


class CargoPlanner(Planner):
    def __init__(self):
        super().__init__()

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
                    score = price / (d ** 1.6)
                    best_deals.append((score, resource, buy, sell))
        return sorted(best_deals, reverse=True, key=lambda tup: tup[0])

    def ship_stuck(self, ship, ship_id):
        if ship.command and ship.command.type == 'trade':
            planet_id = ship.command.target
            planet = self.data.planets[planet_id]
            return planet.position == ship.position
        return False

    def plan(self, ship, ship_id, plan):
        return MoveCommand(destination=Destination(self.get_mothership_coords()))
        if ship.command and not self.ship_stuck(ship, ship_id):
            return
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

        return TradeCommand(target=buy['planet'], resource=resource,
                            amount=min(10 if ship.ship_class == '3' else 40, buy['amount']))
