import pulp
import pandas as pd

# Load data from CSV files
emissions_data = pd.read_csv(
    "india-electricity-plan/indian_electricity_sources_with_emissions.csv"
)
potential_plants_data = pd.read_csv(
    "india-electricity-plan/potential_energy_plants_india.csv"
)
goals_data = pd.read_csv(
    "india-electricity-plan/final_government_goals_2030_with_percent.csv"
)

# Initialize the model
model = pulp.LpProblem("Optimal_Investment_in_Energy_Sources", pulp.LpMinimize)

# Extract relevant data
sources = emissions_data["Source"].tolist()
years = list(range(2024, 2031))

capital_cost = dict(
    zip(emissions_data["Source"], emissions_data["Capital Cost (₹/MW)"])
)
current_capacity = dict(
    zip(emissions_data["Source"], emissions_data["Current Production (MW)"])
)
emission_factors = dict(
    zip(emissions_data["Source"], emissions_data["Emission Factor (kg CO2/kWh)"])
)
capacity_factors = {
    "Solar": 0.2,
    "Wind": 0.3,
    "Hydropower": 0.4,
    "Biomass": 0.7,
    "Nuclear": 0.9,
    "Coal": 0.8,
    "Natural Gas": 0.5,
}

# Convert capacity data to match the sources
goal_mappings = {
    "Coal Capacity (GW)": "Coal",
    "Natural Gas Capacity (GW)": "Natural Gas",
    "Nuclear Capacity (GW)": "Nuclear",
    "Solar Capacity (GW)": "Solar",
    "Wind Capacity (GW)": "Wind",
    "Hydropower Capacity (GW)": "Hydropower",
    "Biomass Capacity (GW)": "Biomass",
}

target_capacity = {
    goal_mappings[row["Goal"]]: row["Target Value"] * 1000
    for _, row in goals_data.iterrows()
    if row["Goal"] in goal_mappings
}

max_plants = dict(
    zip(potential_plants_data["Source"], potential_plants_data["Max Plants"])
)
min_plants = dict(
    zip(potential_plants_data["Source"], potential_plants_data["Min Plants"])
)

# Filter out sources that do not have target capacities
filtered_sources = [source for source in sources if source in target_capacity]

# Decision variables
investment = pulp.LpVariable.dicts(
    "Investment", (filtered_sources, years), lowBound=0, cat="Continuous"
)

# Objective function
model += pulp.lpSum(
    investment[source][year] for source in filtered_sources for year in years
)

# Constraints
total_investment = {}
for source in filtered_sources:
    total_target_cost = (
        target_capacity[source] - current_capacity[source]
    ) * capital_cost[source]
    total_max_cost = max_plants[source] * capital_cost[source]
    total_min_cost = min_plants[source] * capital_cost[source]

    # Ensure the total investment in each source across all years is at least the cost to achieve the target capacity.
    model += pulp.lpSum(investment[source][year] for year in years) >= total_target_cost

    # Ensure the total investment in each source across all years does not exceed the maximum feasible number of plants.
    model += pulp.lpSum(investment[source][year] for year in years) <= total_max_cost

    # Ensure the total investment in each source across all years is at least the minimum number of plants required.
    model += pulp.lpSum(investment[source][year] for year in years) >= total_min_cost

    total_investment[source] = total_target_cost

# Calculate total investment required and average annual investment
total_investment_required = sum(total_investment.values())
average_annual_investment = total_investment_required / len(years)

# Set a range for annual budget, e.g., ±20% of the average annual investment
min_annual_budget = 0.8 * average_annual_investment
max_annual_budget = 1.2 * average_annual_investment

# Ensure that the annual investment does not fall below the minimum annual budget.
for year in years:
    model += (
        pulp.lpSum(investment[source][year] for source in filtered_sources)
        >= min_annual_budget
    )

    # Ensure that the annual investment does not exceed the maximum annual budget.
    model += (
        pulp.lpSum(investment[source][year] for source in filtered_sources)
        <= max_annual_budget
    )

# Renewable capacity and production constraints
renewable_sources = ["Solar", "Wind", "Hydropower", "Biomass"]
total_renewable_capacity_target = sum(
    target_capacity[source] for source in renewable_sources
)
total_renewable_production_target = sum(
    (target_capacity[source] - current_capacity[source])
    * capacity_factors[source]
    * 8760
    / 1e6
    for source in renewable_sources
)

# Ensure that the total renewable capacity across all years meets the target capacity.
model += (
    pulp.lpSum(
        investment[source][year] * (1 / capital_cost[source])
        for source in renewable_sources
        for year in years
    )
    >= total_renewable_capacity_target
)

# Ensure that the total renewable production across all years meets the target production.
model += (
    pulp.lpSum(
        investment[source][year]
        * (1 / capital_cost[source])
        * capacity_factors[source]
        * 8760
        for source in renewable_sources
        for year in years
    )
    >= total_renewable_production_target * 1e6
)

# Emission constraint
total_emission_target = 0.43 * total_renewable_production_target * 1e6 + sum(
    emission_factors[source]
    * (target_capacity[source] - current_capacity[source])
    * capacity_factors[source]
    * 8760
    / 1e3
    for source in filtered_sources
)

# Ensure that the total emissions across all years do not exceed the target emission.
model += (
    pulp.lpSum(
        investment[source][year] * (1 / capital_cost[source]) * emission_factors[source]
        for source in filtered_sources
        for year in years
    )
    <= total_emission_target
)

# Solve the model
model.solve()

# Print the results
for source in filtered_sources:
    for year in years:
        print(
            f"Investment in {source} in {year}: ₹{investment[source][year].varValue:.2f} crore"
        )
    print(f"Average plant size for {source}: {capital_cost[source]} crore/MW")
