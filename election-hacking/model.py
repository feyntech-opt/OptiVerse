from pyomo.environ import *
import pandas as pd
import numpy as np

# Load data from CSV files
factors_importance_df = pd.read_csv("factors_importance_reduced.csv", index_col=0)
wards_to_channels_df = pd.read_csv("wards_to_channels_reduced.csv", index_col=0)
voters_df = pd.read_csv("voters_reduced.csv", index_col=0)
wards_to_regions_df = pd.read_csv("wards_to_regions_reduced.csv", index_col=0)

# Parameters
n_factors = len(factors_importance_df.columns)
n_wards = len(factors_importance_df.index)
n_channels = len(wards_to_channels_df.index)
n_regions = len(wards_to_regions_df["Region"].unique())
B = 1000000  # Total budget
M = 1000000  # Large constant for Big-M method

# Weights for each factor and type of media investment (hypothetical)
alpha = np.random.rand(n_factors)
beta = np.random.rand(n_factors)

# Convert dataframes to numpy arrays for efficiency
factors_importance = factors_importance_df.values
wards_to_channels = wards_to_channels_df.values
voters = voters_df["Voters"].values
wards_to_regions = wards_to_regions_df["Region"].astype("category").cat.codes.values

# Define ward names and other lists for display purposes
wards_names = factors_importance_df.index.tolist()
channels_names = wards_to_channels_df.index.tolist()
regions_names = wards_to_regions_df["Region"].unique().tolist()
factors_names = factors_importance_df.columns.tolist()

# Define model
model = ConcreteModel()

# Decision variables
model.a = Var(range(n_channels), range(n_factors), bounds=(0, None))
model.n = Var(range(n_channels), range(n_factors), bounds=(0, None))
model.k = Var(range(n_regions), range(n_factors), bounds=(0, None))
model.t = Var(range(n_wards), within=Binary)
model.z = Var(range(n_wards), within=Binary)

# Objective function
model.obj = Objective(expr=sum(model.z[w] for w in range(n_wards)), sense=maximize)

# Constraints
model.budget = Constraint(
    expr=sum(
        model.a[c, f] + model.n[c, f]
        for c in range(n_channels)
        for f in range(n_factors)
    )
    + sum(model.k[r, f] for r in range(n_regions) for f in range(n_factors))
    <= B
)

model.allocation_limits = ConstraintList()
for c in range(n_channels):
    for f in range(n_factors):
        model.allocation_limits.add(expr=model.a[c, f] >= 0)
        model.allocation_limits.add(expr=model.n[c, f] >= 0)
for r in range(n_regions):
    for f in range(n_factors):
        model.allocation_limits.add(expr=model.k[r, f] >= 0)

# Winning constraint using Big-M method and hypothetical voter share function
model.winning_constraints = ConstraintList()
for w in range(n_wards):
    total_support = sum(
        (model.a[c, f] + model.n[c, f]) * factors_importance[w, f] * alpha[f]
        for c in range(n_channels)
        for f in range(n_factors)
        if wards_to_channels[c, w] == 1
    ) + sum(
        model.k[wards_to_regions[w], f] * factors_importance[w, f] * beta[f]
        for f in range(n_factors)
    )
    model.winning_constraints.add(
        expr=total_support - 0.5 * voters[w] <= M * (1 - model.z[w])
    )
    model.winning_constraints.add(
        expr=total_support >= 0.5 * voters[w] - M * (1 - model.z[w])
    )

# 2/3 majority constraint
model.majority = Constraint(
    expr=sum(model.z[w] for w in range(n_wards)) >= 2 * n_wards / 3
)

# Solve the model with solver output printed to the console and saved to a file
solver = SolverFactory("glpk")

result = solver.solve(model, tee=True, logfile="solver_output.log")

# Display results
allocation_plan = {
    "Television Ads": np.zeros((n_channels, n_factors)),
    "Newscasting": np.zeros((n_channels, n_factors)),
    "Campaigns": np.zeros((n_regions, n_factors)),
}

for c in range(n_channels):
    for f in range(n_factors):
        allocation_plan["Television Ads"][c, f] = model.a[c, f].value
        allocation_plan["Newscasting"][c, f] = model.n[c, f].value

for r in range(n_regions):
    for f in range(n_factors):
        allocation_plan["Campaigns"][r, f] = model.k[r, f].value

# Create the CSV output
csv_output = pd.DataFrame(
    index=wards_names, columns=factors_names + ["Total Allocation", "Won"]
)

for w in range(n_wards):
    for f in range(n_factors):
        total_allocation = (
            sum(
                (model.a[c, f].value + model.n[c, f].value)
                for c in range(n_channels)
                if wards_to_channels[c, w] == 1
            )
            + model.k[wards_to_regions[w], f].value
        )
        csv_output.at[wards_names[w], factors_names[f]] = total_allocation
    csv_output.at[wards_names[w], "Total Allocation"] = sum(
        csv_output.loc[wards_names[w], factors_names]
    )
    csv_output.at[wards_names[w], "Won"] = "Yes" if model.z[w].value == 1 else "No"

# Save the CSV file
csv_output.to_csv("election_optimization_results.csv")

print("Optimal allocation plan:")
for media, allocations in allocation_plan.items():
    if media in ["Television Ads", "Newscasting"]:
        for c, channel in enumerate(channels_names):
            for f, factor in enumerate(factors_names):
                print(f"{media} - {factor} on {channel}: {allocations[c, f]:.2f}")
    elif media == "Campaigns":
        for r, region in enumerate(regions_names):
            for f, factor in enumerate(factors_names):
                print(f"{media} - {factor} in {region}: {allocations[r, f]:.2f}")

print("Wards won:")
for w in range(n_wards):
    if model.z[w].value == 1:
        print(f"Ward {wards_names[w]}: Won")
    else:
        print(f"Ward {wards_names[w]}: Lost")

print("Total wards won:", sum(model.z[w].value for w in range(n_wards)))
