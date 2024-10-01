import numpy as np
from scipy.optimize import minimize
import pandas as pd

# Load the input data
gross_salaries = pd.read_csv('salary-opt/data/gross_salaries.csv')['Gross Salary'].tolist()

# Define the tax slabs and rates under the current tax regime
tax_slabs = [(0, 250000, 0), (250001, 500000, 0.05), (500001, 1000000, 0.2), (1000001, np.inf, 0.3)]

# Function to calculate tax
def calculate_tax(income):
    tax = 0
    for slab in tax_slabs:
        if income > slab[0]:
            taxable_income = min(income, slab[1]) - slab[0]
            tax += taxable_income * slab[2]
    return tax

# Objective function to minimize tax
def objective(x):
    B, H, S, O, D_80C, D_80D = x
    G = B + H + S + O  # Gross Salary
    standard_deduction = 50000
    metro_city = True
    hra_exemption = min(H, 0.5*B if metro_city else 0.4*B, H - 0.1*B)  # Simplified HRA calculation
    taxable_income = G - standard_deduction - hra_exemption - D_80C - D_80D
    tax_payable = calculate_tax(taxable_income)
    return tax_payable

# Constraints: Sum of all components should be equal to gross salary and within allowed limits
def constraint1(x, gross_salary):
    return sum(x[:4]) - gross_salary

def constraint2(x):
    return 150000 - x[4]  # Section 80C limit

def constraint3(x):
    return 25000 - x[5]  # Section 80D limit for non-senior citizens

# Define a function to perform the optimization for a given gross salary
def optimize_tax(gross_salary):
    # Initial guess for the variables
    x0 = [0.25 * gross_salary, 0.15 * gross_salary, 0.35 * gross_salary, 0.25 * gross_salary, 150000, 25000]

    # Bounds for each component
    bnds = ((0, gross_salary), (0, gross_salary), (0, gross_salary), (0, gross_salary), (0, 150000), (0, 25000))

    # Constraint dictionaries
    con1 = {'type': 'eq', 'fun': constraint1, 'args': (gross_salary,)}
    con2 = {'type': 'ineq', 'fun': constraint2}
    con3 = {'type': 'ineq', 'fun': constraint3}

    constraints = [con1, con2, con3]

    # Perform the optimization
    solution = minimize(objective, x0, bounds=bnds, constraints=constraints)
    return solution.x, solution.fun

# Run the optimization for each gross salary
optimized_results = {}
for salary in gross_salaries:
    optimized_components, tax_payable = optimize_tax(salary)
    optimized_results[salary] = list(optimized_components) + [tax_payable]

# Save the results to a CSV file
df_results = pd.DataFrame(optimized_results).T
df_results.columns = ["Basic Salary", "HRA", "Special Allowance", "Other Components", "Section 80C Deductions", "Section 80D Deductions", "Tax Payable"]
df_results.to_csv('salary-opt/data/optimized_results_test.csv', index_label="Gross Salary")

df_results
