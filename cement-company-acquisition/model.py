import pandas as pd
from ortools.linear_solver import pywraplp

# Read company data
df_companies = pd.read_csv("cement-company-acquisition/companies_data_inr.csv")
df_adani = pd.read_csv("cement-company-acquisition/adani_data_inr.csv")

# Create the optimization solver
solver = pywraplp.Solver.CreateSolver("SCIP")

# Variables for acquisition cost (in INR, example range)
costs = [
    solver.IntVar(
        int(row["Offer Price"] * 0.9), int(row["Offer Price"] * 1.1), f"cost_{i}"
    )
    for i, row in df_companies.iterrows()
]

# Objective: Maximize overall benefit from acquisition
# Weighing factors for different criteria
weights = {
    "Market Share": 0.2,
    "Revenue Growth": 0.15,
    "Production Capacity": 0.15,
    "Cost Structure": 0.1,
    "Compliance Rating": 0.1,
    "Market Regions": 0.1,
    "Number of Plants": 0.1,
    "Integrated Plants": 0.1,
}

# Calculate weighted scores for each company
scores = []
for i in range(len(df_companies)):
    score = (
        weights["Market Share"] * df_companies["Market Share"][i]
        + weights["Revenue Growth"] * df_companies["Revenue Growth"][i]
        + weights["Production Capacity"] * df_companies["Production Capacity"][i]
        + weights["Cost Structure"]
        * (1 / df_companies["Cost Structure"][i])  # Inverse cost structure
        + weights["Compliance Rating"] * df_companies["Compliance Rating"][i]
        + weights["Market Regions"] * df_companies["Market Regions"][i]
        + weights["Number of Plants"] * df_companies["Number of Plants"][i]
        + weights["Integrated Plants"] * df_companies["Integrated Plants"][i]
    )
    scores.append(score)

# Add constraints to ensure the solver chooses only one company
selection = [solver.IntVar(0, 1, f"select_{i}") for i in range(len(df_companies))]
solver.Add(sum(selection) == 1)

# Objective function
solver.Maximize(
    sum(selection[i] * scores[i] - costs[i] for i in range(len(df_companies)))
)

# Solve the problem
status = solver.Solve()

# Prepare results
results = []
if status == pywraplp.Solver.OPTIMAL:
    for i in range(len(df_companies)):
        if selection[i].solution_value() == 1:
            results.append(
                {
                    "Selected Company": df_companies["Company"][i],
                    "Acquisition Cost (INR)": costs[i].solution_value(),
                    "Score": scores[i],
                }
            )

# Display results
if results:
    for result in results:
        print(f"Selected Company: {result['Selected Company']}")
        print(f"Acquisition Cost (INR): {result['Acquisition Cost (INR)']}")
        print(f"Score: {result['Score']}")
else:
    print("No optimal solution found.")
