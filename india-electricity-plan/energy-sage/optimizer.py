# optimizer.py

from gurobipy import GRB
from config import TIME_LIMIT, MIP_GAP


def optimize_model(model, data, investment, capacity_slack, total_capacity_var, total_capacity_slack, source_used, total_production):
    # Set solver parameters
    model.Params.TimeLimit = TIME_LIMIT
    model.Params.MIPGap = MIP_GAP

    # Optimize
    model.optimize()

    if model.status == GRB.OPTIMAL or model.status == GRB.TIME_LIMIT:
        results = {}
        results['total_investment'] = sum(investment[s, y].X * data['capital_cost'][s][y]
                                          for s in data['sources'] for y in data['years'])
        results['total_capacity'] = total_capacity_var.X
        results['capacity_shortfall'] = total_capacity_slack.X
        results['total_production'] = total_production.X
        results['max_theoretical_production'] = sum(
            (data['current_capacity'][s] + sum(investment[s, y].X for y in data['years'])) * 8760 / 1e6 for s in data['sources'])

        renewable_sources = ["Solar", "Wind", "Hydropower", "Waste to Energy"]
        results['renewable_capacity'] = sum(data['current_capacity'][s] +
                                            sum(investment[s, y].X for y in data['years']) for s in renewable_sources)

        results['total_emissions'] = sum((data['current_capacity'][s] + sum(investment[s, y].X for y in data['years']))
                                         * 1000 * data['emission_factors'][s] * data['capacity_factors'][s] * 8760 for s in data['sources'])
        current_emissions = sum(data['current_capacity'][s] * 1000 * data['emission_factors']
                                [s] * data['capacity_factors'][s] * 8760 for s in data['sources'])
        results['emissions_change'] = (results['total_emissions'] / current_emissions - 1) * 100

        results['source_investments'] = {}
        for s in data['sources']:
            total_source_investment = sum(investment[s, y].X * data['capital_cost'][s][y] for y in data['years'])
            if total_source_investment > 0:
                results['source_investments'][s] = {
                    'total_investment': total_source_investment,
                    'yearly_investments': {y: investment[s, y].X * data['capital_cost'][s][y] for y in data['years'] if investment[s, y].X > 0},
                    'capacity_addition': sum(investment[s, y].X for y in data['years']),
                    'final_capacity': data['current_capacity'][s] + sum(investment[s, y].X for y in data['years']),
                    'capacity_factor': data['capacity_factors'][s],
                    'annual_production': (data['current_capacity'][s] + sum(investment[s, y].X for y in data['years'])) * data['capacity_factors'][s] * 8760 / 1e6,
                    'min_capacity': data['min_capacity'].get(s, 'N/A'),
                    'max_capacity': data['max_capacity'].get(s, 'N/A'),
                    'capacity_shortfall': capacity_slack[s].X if capacity_slack[s].X > 0 else 0
                }

        return results
    else:
        return None
