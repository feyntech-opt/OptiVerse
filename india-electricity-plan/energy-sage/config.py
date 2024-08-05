# config.py

# File paths
EMISSIONS_DATA_PATH = "india-electricity-plan/indian_electricity_sources_with_emissions.csv"
CAPACITY_BOUNDS_PATH = "india-electricity-plan/source_based_capacity_bounds.csv"
CAPITAL_COSTS_PATH = "india-electricity-plan/projected_capital_costs_2024_2028_million_inr_per_mw.csv"

# Time range
START_YEAR = 2024
END_YEAR = 2030

# Budget constraints
TOTAL_BUDGET = 60e11  # 60 lakh crore INR
YEARLY_BUDGET_FRACTION = 0.25

# Capacity constraints
MIN_TOTAL_CAPACITY = 800000  # MW
MAX_TOTAL_CAPACITY = 950000  # MW

# Renewable energy target
RENEWABLE_TARGET = 0.4  # 40% of total capacity

# Emissions constraint
EMISSIONS_INCREASE_LIMIT = 0.0  # 0% increase allowed

# Diversity constraint
MIN_SOURCES_USED = 3

# Objective function weights
TOTAL_CAPACITY_PENALTY = 1e10
CAPACITY_PENALTY = 1e6
DIVERSITY_INCENTIVE = 1e7
PRODUCTION_WEIGHT = 1e-2

# Solver parameters
TIME_LIMIT = 3600  # 1 hour
MIP_GAP = 0.01  # 1% optimality gap
