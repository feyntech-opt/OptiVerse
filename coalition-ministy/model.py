from ortools.sat.python import cp_model
import pandas as pd

# Load the budget data
budget_data_path = "India_Ministries_Budget_2024-25.csv"
budget_df = pd.read_csv(budget_data_path)

# Coalition data
coalition_data = {
    "Party name": [
        "Bharatiya Janata Party",
        "All Jharkhand Students Union",
        "Apna Dal (Soneylal)",
        "Asom Gana Parishad",
        "Hill State People's Democratic Party",
        "Janata Dal (Secular)",
        "Janata Dal (United)",
        "Lok Janshakti Party (Ram Vilas)",
        "Nationalist Congress Party",
        "Shiv Sena",
        "Sikkim Krantikari Morcha",
        "Telugu Desam Party",
        "United People's Party Liberal",
        "Hindustani Awam Morcha",
        "Jana Sena Party",
        "Rashtriya Lok Dal",
    ],
    "Abbreviation": [
        "BJP",
        "AJSUP",
        "AD(S)",
        "AGP",
        "HSPDP",
        "JD(S)",
        "JD(U)",
        "LJPRV",
        "NCP",
        "SHS",
        "SKM",
        "TDP",
        "UPPL",
        "HAM",
        "JSP",
        "RLD",
    ],
    "Lok Sabha seats": [240, 1, 1, 1, 0, 2, 12, 5, 1, 7, 1, 16, 1, 1, 2, 2],
}

coalition_df = pd.DataFrame(coalition_data)
coalition_df = coalition_df[
    coalition_df["Lok Sabha seats"] > 0
]  # Exclude parties with 0 seats

# Set all non-BJP parties as critical
coalition_df["Critical"] = coalition_df["Abbreviation"] != "BJP"

# Calculate the influence factor for each party
total_seats = coalition_df["Lok Sabha seats"].sum()
coalition_df["Influence Factor"] = total_seats / coalition_df["Lok Sabha seats"]
coalition_df.loc[coalition_df["Abbreviation"] == "BJP", "Influence Factor"] = (
    1  # BJP does not get an enhanced influence
)

# Cap influence factors to prevent excessive dominance by small parties
max_influence_factor = 3
coalition_df["Influence Factor"] = coalition_df["Influence Factor"].apply(
    lambda x: min(x, max_influence_factor)
)

# Prepare the model
model = cp_model.CpModel()

# Define variables for each ministry-party assignment
ministry_vars = {}
for ministry in budget_df["Ministry"]:
    for party in coalition_df["Abbreviation"]:
        ministry_vars[(ministry, party)] = model.NewBoolVar(f"{ministry}_{party}")

# Each ministry is assigned to exactly one party
for ministry in budget_df["Ministry"]:
    model.Add(
        sum(ministry_vars[(ministry, party)] for party in coalition_df["Abbreviation"])
        == 1
    )

# Create a boolean variable to indicate if a party gets any ministry
party_has_ministry = {
    party: model.NewBoolVar(f"{party}_has_ministry")
    for party in coalition_df["Abbreviation"]
}

# Ensure that if a party gets any ministry, the boolean variable is set to 1
for party in coalition_df["Abbreviation"]:
    model.Add(
        sum(ministry_vars[(ministry, party)] for ministry in budget_df["Ministry"]) > 0
    ).OnlyEnforceIf(party_has_ministry[party])
    model.Add(
        sum(ministry_vars[(ministry, party)] for ministry in budget_df["Ministry"]) == 0
    ).OnlyEnforceIf(party_has_ministry[party].Not())

# Constraint: Total budget allocation should be proportional to seat strength with some tolerance
total_budget = budget_df["Budget Allocation (₹ Crore)"].sum()

# Scale up the total budget to avoid floating point arithmetic issues
scale_factor = 1000
total_budget_scaled = int(total_budget * scale_factor)

# Set a tolerance level (e.g., 25%) to ensure flexibility
tolerance = 0.25

for index, row in coalition_df.iterrows():
    party = row["Abbreviation"]
    party_seats = row["Lok Sabha seats"]
    influence_factor = row["Influence Factor"]
    party_min_budget = int(
        (party_seats / total_seats)
        * total_budget_scaled
        * (1 - tolerance)
        * influence_factor
    )
    party_max_budget = int(
        (party_seats / total_seats)
        * total_budget_scaled
        * (1 + tolerance)
        * influence_factor
    )
    budget_allocation = sum(
        ministry_vars[(ministry, party)]
        * int(
            budget_df[budget_df["Ministry"] == ministry][
                "Budget Allocation (₹ Crore)"
            ].values[0]
            * scale_factor
        )
        for ministry in budget_df["Ministry"]
    )
    model.Add(budget_allocation <= party_max_budget)
    model.Add(budget_allocation >= party_min_budget).OnlyEnforceIf(
        party_has_ministry[party]
    )

# Ensure BJP gets a minimum number of ministries
min_ministries_for_bjp = max(
    3, len(budget_df) // 4
)  # Ensure BJP gets at least a quarter of the ministries
model.Add(
    sum(ministry_vars[(ministry, "BJP")] for ministry in budget_df["Ministry"])
    >= min_ministries_for_bjp
)

# Ensure every significant party gets at least one ministry
for party in coalition_df["Abbreviation"]:
    if party != "BJP":
        model.Add(
            sum(ministry_vars[(ministry, party)] for ministry in budget_df["Ministry"])
            >= 1
        ).OnlyEnforceIf(party_has_ministry[party])

# Limit the number of ministries any single party can hold to prevent over-concentration
max_ministries_per_party = (
    len(budget_df) // 2
)  # Ensure no party gets more than half of the ministries
for party in coalition_df["Abbreviation"]:
    model.Add(
        sum(ministry_vars[(ministry, party)] for ministry in budget_df["Ministry"])
        <= max_ministries_per_party
    )

# Objective: Maximize the number of parties with at least one ministry
model.Maximize(sum(party_has_ministry[party] for party in coalition_df["Abbreviation"]))

# Solve the model
solver = cp_model.CpSolver()
status = solver.Solve(model)

# Check if a feasible solution is found
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    allocation = []
    for ministry in budget_df["Ministry"]:
        for party in coalition_df["Abbreviation"]:
            if solver.BooleanValue(ministry_vars[(ministry, party)]):
                allocation.append([ministry, party])
    # Convert the allocation to a DataFrame and save as CSV
    allocation_df = pd.DataFrame(allocation, columns=["Ministry", "Assigned Party"])
    allocation_csv_path = "Ministry_Allocation.csv"
    allocation_df.to_csv(allocation_csv_path, index=False)
    print(f"Ministry allocations saved to {allocation_csv_path}")
else:
    print("No feasible solution found")
