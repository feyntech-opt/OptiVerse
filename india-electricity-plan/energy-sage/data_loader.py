# data_loader.py

import pandas as pd
from config import *

def load_data():
    emissions_data = pd.read_csv(EMISSIONS_DATA_PATH)
    capacity_bounds_data = pd.read_csv(CAPACITY_BOUNDS_PATH)
    capital_costs_data = pd.read_csv(CAPITAL_COSTS_PATH)

    sources = emissions_data["Source"].tolist()
    years = list(range(START_YEAR, END_YEAR + 1))
    current_capacity = dict(zip(emissions_data["Source"], emissions_data["Current Production (MW)"]))
    emission_factors = dict(zip(emissions_data["Source"], emissions_data["Emission Factor (kg CO2/kWh)"]))
    capacity_factors = dict(zip(emissions_data["Source"], emissions_data["Capacity Factor (%)"] / 100))

    # Process capital costs (convert million rupees to rupees)
    capital_cost = {source: {} for source in sources}
    for _, row in capital_costs_data.iterrows():
        source = row['Source']
        for year in range(START_YEAR, 2029):
            capital_cost[source][year] = row[str(year)] * 1e6  # Convert million rupees to rupees
        # Extend to 2029 and 2030 with the same value as 2028
        capital_cost[source][2029] = capital_cost[source][2028]
        capital_cost[source][2030] = capital_cost[source][2028]

    # Capacity bounds
    min_capacity = {row["Source"]: row["Min Capacity (GW)"] * 1000 for _, row in capacity_bounds_data.iterrows()}
    max_capacity = {row["Source"]: row["Max Capacity (GW)"] * 1000 for _, row in capacity_bounds_data.iterrows()}

    return {
        'sources': sources,
        'years': years,
        'current_capacity': current_capacity,
        'emission_factors': emission_factors,
        'capacity_factors': capacity_factors,
        'capital_cost': capital_cost,
        'min_capacity': min_capacity,
        'max_capacity': max_capacity
    }