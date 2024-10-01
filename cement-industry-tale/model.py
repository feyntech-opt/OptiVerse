import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pulp import *
from IPython.display import display, HTML

# Set random seed for reproducibility
np.random.seed(42)

# Market parameters
num_periods = 12  # Monthly data for a year
a = 10000  # Base price (rupees per ton)
b = 0.1    # Price sensitivity

# Company-specific parameters
companies = ['Adani', 'UltraTech']
base_costs = {'Adani': 3000, 'UltraTech': 3200}  # Base production cost (rupees per ton)
max_capacity = {'Adani': 150, 'UltraTech': 150}  # Maximum monthly production capacity (million tons)
min_production = {'Adani': 80, 'UltraTech': 80}  # Minimum monthly production (million tons)

# Random factors
seasonality = 1 + 0.2 * np.sin(np.linspace(0, 2*np.pi, num_periods))  # Seasonal demand fluctuation
cost_fluctuation = np.random.uniform(0.9, 1.1, (len(companies), num_periods))  # Random cost fluctuations

def calculate_nash_equilibrium(df_production):
    nash_equilibria = []
    for month in df_production.index:
        production_adani = df_production.loc[month, 'Adani']
        production_ultratech = df_production.loc[month, 'UltraTech']
        total_production = production_adani + production_ultratech
        price = a - b * total_production
        
        # Check if neither company can profitably deviate
        profit_adani = price * production_adani - base_costs['Adani'] * production_adani
        profit_ultratech = price * production_ultratech - base_costs['UltraTech'] * production_ultratech
        
        # Simple check: if production is between min and max, and profits are positive, consider it Nash equilibrium
        if (min_production['Adani'] <= production_adani <= max_capacity['Adani'] and
            min_production['UltraTech'] <= production_ultratech <= max_capacity['UltraTech'] and
            profit_adani > 0 and profit_ultratech > 0):
            nash_equilibria.append((month, production_adani, production_ultratech))
    
    return nash_equilibria

# Create optimization problem
prob = LpProblem("Cement_Industry_Optimization", LpMaximize)

# Define variables
production = LpVariable.dicts("Production", [(i, t) for i in companies for t in range(num_periods)], lowBound=0)
total_production = LpVariable.dicts("TotalProduction", range(num_periods), lowBound=0)
revenue = LpVariable.dicts("Revenue", range(num_periods), lowBound=0)

# Piecewise linear approximation
num_segments = 10
max_total_production = sum(max_capacity.values())
segment_size = max_total_production / num_segments
lambdas = LpVariable.dicts("lambda", [(t, s) for t in range(num_periods) for s in range(num_segments)], lowBound=0, upBound=1)

# Objective function
prob += lpSum(revenue[t] - lpSum(base_costs[i] * cost_fluctuation[companies.index(i), t] * production[i, t] for i in companies)
               for t in range(num_periods))

# Constraints
for t in range(num_periods):
    # Total production constraint
    prob += total_production[t] == lpSum(production[i, t] for i in companies)
    
    # Piecewise linear approximation constraints
    prob += lpSum(lambdas[t, s] for s in range(num_segments)) == 1
    prob += total_production[t] == lpSum(s * segment_size * lambdas[t, s] for s in range(num_segments))
    prob += revenue[t] == lpSum((a - b * s * segment_size) * s * segment_size * lambdas[t, s] for s in range(num_segments))
    
    for i in companies:
        # Capacity constraint with seasonality
        prob += production[i, t] <= max_capacity[i] * seasonality[t]
        # Minimum production constraint
        prob += production[i, t] >= min_production[i]

# Solve the problem
prob.solve()

# Extract results
results = {i: [production[i, t].varValue for t in range(num_periods)] for i in companies}
df_production = pd.DataFrame(results, index=[f'Month {t+1}' for t in range(num_periods)])

# After solving the problem and creating df_production, add:
nash_points = calculate_nash_equilibrium(df_production)
print("\nNash Equilibrium Points:")
for point in nash_points:
    print(f"Month {point[0]}: Adani - {point[1]:.2f}, UltraTech - {point[2]:.2f}")

# Calculate market price and profits
total_prod = df_production.sum(axis=1)
market_price = a - b * total_prod
df_price = pd.DataFrame({'Market Price': market_price})

profits = {}
for i in companies:
    company_production = df_production[i]
    company_costs = base_costs[i] * cost_fluctuation[companies.index(i), :] * company_production
    company_revenue = market_price * company_production
    profits[i] = company_revenue - company_costs

df_profits = pd.DataFrame(profits)

# Visualizations
plt.figure(figsize=(12, 6))
df_production.plot(kind='bar', stacked=True)
plt.title("Monthly Cement Production")
plt.xlabel("Month")
plt.ylabel("Production (Million Tons)")
plt.legend(title="Company")
plt.tight_layout()
plt.show()

plt.figure(figsize=(12, 6))
df_profits.plot(kind='line', marker='o')
plt.title("Monthly Profits")
plt.xlabel("Month")
plt.ylabel("Profit (Million Rupees)")
plt.legend(title="Company")
plt.grid(True)
plt.tight_layout()
plt.show()

plt.figure(figsize=(12, 6))
sns.heatmap(df_production.corr(), annot=True, cmap='coolwarm')
plt.title("Production Correlation Heatmap")
plt.tight_layout()
plt.show()

# Display summary statistics
summary = df_production.describe()
display(HTML(summary.to_html()))

