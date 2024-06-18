
# Optimal Investment in Energy Sources for India (2024-2030)

## Overview

This project aims to determine the optimal annual investment in various energy sources in India from 2024 to 2030 to achieve the government's energy goals. The model takes into consideration capital costs, capacity, production targets, and emissions constraints.

## Data Files

1. **indian_electricity_sources_with_emissions.csv**:
   - Contains data on various energy sources, including capital costs, current production, and emission factors. [Source: CEA - Central Electricity Authority](https://cea.nic.in/cdm-co2-baseline-database/)

2. **potential_energy_plants_india.csv**:
   - Provides information on the potential number of plants that can be built for each energy source, including maximum and minimum feasible numbers. [Source: Ministry of Power, Government of India](https://powermin.gov.in/en/content/power-sector-glance-all-india)

3. **final_government_goals_2030_with_percent.csv**:
   - Lists the government's target values for 2030, including capacities and production for different energy sources. [Source: Ministry of Statistics and Program Implementation](https://mospi.gov.in/web/mospi/energy-statistics)

## Model Description

The optimization model uses the PuLP library to minimize the total investment cost required to achieve the government's energy targets while adhering to the constraints on capacity, production, and emissions.

## Decision Variables

- **Investment**: I_{s,t} represents the investment in source s in year t (in crore ₹).

## Objective Function

Minimize the total cost of investments over the planning period (2024-2030).

Minimize ∑_{s} ∑_{t} I_{s,t}

## Constraints

### Total Target Cost Constraint
Ensures the total investment in each source across all years is at least the cost required to achieve the target capacity.

∑_{t=2024}^{2030} I_{s,t} ≥ (target_capacity[s] - current_capacity[s]) * capital_cost[s]

### Maximum Feasible Investment Constraint
Ensures the total investment in each source across all years does not exceed the maximum feasible number of plants.

∑_{t=2024}^{2030} I_{s,t} ≤ max_plants[s] * capital_cost[s]

### Minimum Investment Constraint
Ensures the total investment in each source across all years is at least the minimum number of plants required.

∑_{t=2024}^{2030} I_{s,t} ≥ min_plants[s] * capital_cost[s]

### Annual Budget Constraints
Ensures that the annual investment does not fall below the minimum annual budget.

∑_{s} I_{s,t} ≥ min_annual_budget

Ensures that the annual investment does not exceed the maximum annual budget.

∑_{s} I_{s,t} ≤ max_annual_budget

### Total Renewable Capacity Constraint
Ensures that the total renewable capacity across all years meets the target capacity.

∑_{s ∈ renewable_sources} ∑_{t=2024}^{2030} (I_{s,t} / capital_cost[s]) ≥ total_renewable_capacity_target

### Total Renewable Production Constraint
Ensures that the total renewable production across all years meets the target production.

∑_{s ∈ renewable_sources} ∑_{t=2024}^{2030} (I_{s,t} / capital_cost[s]) * capacity_factors[s] * 8760 ≥ total_renewable_production_target * 10^6

### Emission Constraint
Ensures that the total emissions across all years do not exceed the target emission.

∑_{s} ∑_{t=2024}^{2030} (I_{s,t} / capital_cost[s]) * emission_factors[s] ≤ total_emission_target

## How to Run the Model

1. **Install Dependencies**:
   - Ensure you have Python installed along with the PuLP library.

   ```bash
   pip install pulp pandas
   ```

2. **Prepare Data Files**:
   - Ensure the CSV files (`indian_electricity_sources_with_emissions.csv`, `potential_energy_plants_india.csv`, `final_government_goals_2030_with_percent.csv`) are in the correct directory.

3. **Run the Script**:
   - Execute the script to run the optimization model.

   ```bash
   python model.py
   ```

4. **Results**:
   - The script will print the investment required in each energy source for each year and the average plant size.

## References

- Data sources for Indian electricity production and emissions: [Central Electricity Authority - CDM CO2 Baseline Database](https://cea.nic.in/cdm-co2-baseline-database/)
- Potential energy plants in India: [Power Sector at a Glance - Ministry of Power](https://powermin.gov.in/en/content/power-sector-glance-all-india)
- Government goals for 2030: [Energy Statistics India 2023 - Ministry of Statistics and Program Implementation](https://mospi.gov.in/web/mospi/energy-statistics)
