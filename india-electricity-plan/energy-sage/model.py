import gurobipy as gp
from gurobipy import GRB

def create_model(data, params):
    model = gp.Model("India_Energy_Transition_Yearly_Costs")

    # Unpack data
    sources = data['sources']
    years = data['years']
    current_capacity = data['current_capacity']
    emission_factors = data['emission_factors']
    capacity_factors = data['capacity_factors']
    capital_cost = data['capital_cost']
    min_capacity = data['min_capacity']
    max_capacity = data['max_capacity']

    # Decision variables
    investment = model.addVars(sources, years, name="Investment", lb=0.0)
    capacity_slack = model.addVars(sources, name="Capacity_Slack", lb=0.0)
    total_capacity_var = model.addVar(name="Total_Capacity")
    total_capacity_slack = model.addVar(name="Total_Capacity_Slack", lb=0.0)
    source_used = model.addVars(sources, vtype=GRB.BINARY, name="Source_Used")
    total_production = model.addVar(name="Total_Annual_Production")

    # Objective function
    model.setObjective(
        params['TOTAL_CAPACITY_PENALTY'] * total_capacity_slack +
        params['CAPACITY_PENALTY'] * gp.quicksum(capacity_slack[s] for s in sources) +
        gp.quicksum(investment[s, y] * capital_cost[s][y] for s in sources for y in years) -
        params['DIVERSITY_INCENTIVE'] * gp.quicksum(source_used[s] for s in sources) -
        params['PRODUCTION_WEIGHT'] * total_production,
        GRB.MINIMIZE
    )

    # Constraints
    model.addConstr(gp.quicksum(investment[s, y] * capital_cost[s][y] for s in sources for y in years) <= params['TOTAL_BUDGET'], "Total_Budget")

    for y in years:
        model.addConstr(gp.quicksum(investment[s, y] * capital_cost[s][y] for s in sources) <= params['YEARLY_BUDGET_FRACTION'] * params['TOTAL_BUDGET'], f"Yearly_Budget_{y}")

    for s in sources:
        if s in min_capacity:
            model.addConstr(
                current_capacity[s] + gp.quicksum(investment[s, y] for y in years) + capacity_slack[s] >= min_capacity[s],
                f"Min_Capacity_{s}"
            )
        if s in max_capacity:
            model.addConstr(
                current_capacity[s] + gp.quicksum(investment[s, y] for y in years) <= max_capacity[s],
                f"Max_Capacity_{s}"
            )
        model.addConstr(gp.quicksum(investment[s, y] for y in years) <= source_used[s] * 1e6, f"Link_Source_Used_{s}")
        model.addConstr(gp.quicksum(investment[s, y] * capital_cost[s][y] for y in years) <= 0.4 * params['TOTAL_BUDGET'], f"Max_Investment_{s}")

    model.addConstr(
        gp.quicksum(current_capacity[s] + gp.quicksum(investment[s, y] for y in years) for s in sources) == total_capacity_var,
        "Total_Capacity_Calculation"
    )
    model.addConstr(total_capacity_var + total_capacity_slack >= params['MIN_TOTAL_CAPACITY'], "Min_Total_Capacity")
    model.addConstr(total_capacity_var <= params['MAX_TOTAL_CAPACITY'], "Max_Total_Capacity")

    renewable_sources = ["Solar", "Wind", "Hydropower", "Waste to Energy"]
    model.addConstr(
        gp.quicksum(current_capacity[s] + gp.quicksum(investment[s, y] for y in years) for s in renewable_sources) >=
        params['RENEWABLE_TARGET'] * total_capacity_var,
        "Renewable_Target"
    )

    current_emissions = sum(current_capacity[s] * 1000 * emission_factors[s] * capacity_factors[s] * 8760 for s in sources)
    model.addConstr(
        gp.quicksum((current_capacity[s] + gp.quicksum(investment[s, y] for y in years)) * 1000 * emission_factors[s] * capacity_factors[s] * 8760 for s in sources) 
        <= (1 + params['EMISSIONS_INCREASE_LIMIT']) * current_emissions,
        "Emissions_Limit"
    )

    model.addConstr(gp.quicksum(source_used[s] for s in sources) >= params['MIN_SOURCES_USED'], "Min_Sources_Used")

    model.addConstr(
        total_production == gp.quicksum((current_capacity[s] + gp.quicksum(investment[s, y] for y in years)) * capacity_factors[s] * 8760 / 1e6 for s in sources),
        "Total_Annual_Production_Calculation"
    )

    return model, investment, capacity_slack, total_capacity_var, total_capacity_slack, source_used, total_production