import gurobipy as gp
from gurobipy import GRB
import pandas as pd

# Load data
emissions_data = pd.read_csv("india-electricity-plan/indian_electricity_sources_with_emissions.csv")
capacity_bounds_data = pd.read_csv("india-electricity-plan/source_based_capacity_bounds.csv")
capital_costs_data = pd.read_csv("india-electricity-plan/projected_capital_costs_2024_2028_million_inr_per_mw.csv")

# Initialize model
model = gp.Model("India_Energy_Transition_Yearly_Costs")

# Parameters
sources = emissions_data["Source"].tolist()
years = list(range(2024, 2031))
current_capacity = dict(zip(emissions_data["Source"], emissions_data["Current Production (MW)"]))
emission_factors = dict(zip(emissions_data["Source"], emissions_data["Emission Factor (kg CO2/kWh)"]))
capacity_factors = dict(zip(emissions_data["Source"], emissions_data["Capacity Factor (%)"] / 100))

# Process capital costs (convert million rupees to rupees)
capital_cost = {source: {} for source in sources}
for _, row in capital_costs_data.iterrows():
    source = row['Source']
    for year in range(2024, 2029):
        capital_cost[source][year] = row[str(year)] * 1e6  # Convert million rupees to rupees
    # Extend to 2029 and 2030 with the same value as 2028
    capital_cost[source][2029] = capital_cost[source][2028]
    capital_cost[source][2030] = capital_cost[source][2028]

# Capacity bounds
min_capacity = {row["Source"]: row["Min Capacity (GW)"] * 1000 for _, row in capacity_bounds_data.iterrows()}
max_capacity = {row["Source"]: row["Max Capacity (GW)"] * 1000 for _, row in capacity_bounds_data.iterrows()}

# Decision variables
investment = model.addVars(sources, years, name="Investment", lb=0.0)
capacity_slack = model.addVars(sources, name="Capacity_Slack", lb=0.0)
total_capacity_var = model.addVar(name="Total_Capacity")
total_capacity_slack = model.addVar(name="Total_Capacity_Slack", lb=0.0)
source_used = model.addVars(sources, vtype=GRB.BINARY, name="Source_Used")

# New variable for total annual production
total_production = model.addVar(name="Total_Annual_Production")

# Multi-objective function
total_capacity_penalty = 1e10
capacity_penalty = 1e6
diversity_incentive = 1e7
production_weight = 1e-2  # Weight for production maximization

# Update the objective function and constraints
model.setObjective(
    total_capacity_penalty * total_capacity_slack +
    capacity_penalty * gp.quicksum(capacity_slack[s] for s in sources) +
    gp.quicksum(investment[s, y] * capital_cost[s][y] for s in sources for y in years) -
    diversity_incentive * gp.quicksum(source_used[s] for s in sources) -
    production_weight * total_production,
    GRB.MINIMIZE
)

# Constraints
total_budget = 60e11  # 60 lakh crore INR
model.addConstr(gp.quicksum(investment[s, y] * capital_cost[s][y] for s in sources for y in years) <= total_budget, "Total_Budget")

yearly_budget = 0.25 * total_budget
for y in years:
    model.addConstr(gp.quicksum(investment[s, y] * capital_cost[s][y] for s in sources) <= yearly_budget, f"Yearly_Budget_{y}")

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
    model.addConstr(gp.quicksum(investment[s, y] * capital_cost[s][y] for y in years) <= 0.4 * total_budget, f"Max_Investment_{s}")

model.addConstr(
    gp.quicksum(current_capacity[s] + gp.quicksum(investment[s, y] for y in years) for s in sources) == total_capacity_var,
    "Total_Capacity_Calculation"
)
model.addConstr(total_capacity_var + total_capacity_slack >= 800000, "Min_Total_Capacity")
model.addConstr(total_capacity_var <= 950000, "Max_Total_Capacity")

renewable_sources = ["Solar", "Wind", "Hydropower", "Waste to Energy"]
model.addConstr(
    gp.quicksum(current_capacity[s] + gp.quicksum(investment[s, y] for y in years) for s in renewable_sources) >=
    0.4 * total_capacity_var,
    "Renewable_Target"
)

current_emissions = sum(current_capacity[s] * 1000 * emission_factors[s] * capacity_factors[s] * 8760 for s in sources)
model.addConstr(
    gp.quicksum((current_capacity[s] + gp.quicksum(investment[s, y] for y in years)) * 1000 * emission_factors[s] * capacity_factors[s] * 8760 for s in sources) <= current_emissions,
    "Emissions_Limit"
)

model.addConstr(gp.quicksum(source_used[s] for s in sources) >= 3, "Min_Sources_Used")

model.addConstr(
    total_production == gp.quicksum((current_capacity[s] + gp.quicksum(investment[s, y] for y in years)) * capacity_factors[s] * 8760 / 1e6 for s in sources),
    "Total_Annual_Production_Calculation"
)

# Optimize
model.optimize()

# Print results
if model.status == GRB.OPTIMAL:
    print("\nOptimal solution found:")
    total_investment = sum(investment[s, y].X * capital_cost[s][y] for s in sources for y in years)
    print(f"Total Investment: ₹{total_investment / 1e11:.2f} lakh crore")
    
    print(f"Total Capacity: {total_capacity_var.X:.2f} MW")
    if total_capacity_slack.X > 0:
        print(f"Total Capacity Shortfall: {total_capacity_slack.X:.2f} MW")
    
    print(f"Total Annual Production: {total_production.X:.2f} TWh")
    max_theoretical_production = sum((current_capacity[s] + sum(investment[s, y].X for y in years)) * 8760 / 1e6 for s in sources)
    print(f"Maximum Theoretical Annual Production: {max_theoretical_production:.2f} TWh")
    
    renewable_capacity = sum(current_capacity[s] + sum(investment[s, y].X for y in years) for s in renewable_sources)
    print(f"Renewable Capacity: {renewable_capacity:.2f} MW ({renewable_capacity/total_capacity_var.X*100:.2f}%)")
    
    total_emissions = sum((current_capacity[s] + sum(investment[s, y].X for y in years)) * 1000 * emission_factors[s] * capacity_factors[s] * 8760 for s in sources)
    print(f"Total Annual Emissions: {total_emissions:.2f} kg CO2")
    print(f"Emissions Change: {((total_emissions/current_emissions)-1)*100:.2f}%")
    
    for s in sources:
        total_source_investment = sum(investment[s, y].X * capital_cost[s][y] for y in years)
        if total_source_investment > 0:
            print(f"\n{s}:")
            for y in years:
                if investment[s, y].X > 0:
                    print(f"  {y}: ₹{investment[s, y].X * capital_cost[s][y] / 1e11:.2f} lakh crore")
            print(f"  Total: ₹{total_source_investment / 1e11:.2f} lakh crore")
            capacity_addition = sum(investment[s, y].X for y in years)
            final_capacity = current_capacity[s] + capacity_addition
            print(f"  Capacity Addition: {capacity_addition:.2f} MW")
            print(f"  Final Capacity: {final_capacity:.2f} MW")
            print(f"  Capacity Factor: {capacity_factors[s]:.2f}")
            production = final_capacity * capacity_factors[s] * 8760 / 1e6  # Annual production in TWh
            print(f"  Annual Production: {production:.2f} TWh")
            if s in min_capacity:
                print(f"  Min Capacity: {min_capacity[s]:.2f} MW")
            if s in max_capacity:
                print(f"  Max Capacity: {max_capacity[s]:.2f} MW")
            if capacity_slack[s].X > 0:
                print(f"  Capacity Shortfall: {capacity_slack[s].X:.2f} MW")
else:
    print("No optimal solution found. Status:", model.status)