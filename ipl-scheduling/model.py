import pandas as pd
import numpy as np
from ortools.sat.python import cp_model

# Load the CSV files
matches_df = pd.read_csv('ipl_matches.csv')
venues_df = pd.read_csv('ipl_venues.csv')
distance_df = pd.read_csv('distance_matrix.csv', index_col=0)
# Assuming we are setting the availability matrix to all 1s for simplicity
availability_df = pd.DataFrame(1, index=[f'Stadium_{i+1}' for i in range(10)], columns=[f'Day_{i+1}' for i in range(60)])

# Convert the availability DataFrame to a dictionary for easy access
availability_dict = availability_df.to_dict()

# Define the distance matrix from the DataFrame
distance_matrix = distance_df.values

# Define the model
model = cp_model.CpModel()

# Parameters
teams = matches_df['Team_1'].unique()
num_teams = len(teams)
num_stadiums = len(venues_df)
num_days = len(availability_df.columns)
max_matches_per_day = 1

# Create a mapping for teams and stadiums
team_index = {team: i for i, team in enumerate(teams)}
stadium_index = {stadium: i for i, stadium in enumerate(venues_df['Stadium'])}

# Variables
matches = {}
for t1 in range(num_teams):
    for t2 in range(t1 + 1, num_teams):
        for s in range(num_stadiums):
            for d in range(num_days):
                matches[(t1, t2, s, d)] = model.NewBoolVar(f'match_{t1}_{t2}_{s}_{d}')

# Constraints
# 1. Team availability and logistics
for t in range(num_teams):
    for d in range(num_days):
        model.Add(sum(matches[(min(t, t2), max(t, t2), s, d)] for t2 in range(num_teams) if t != t2 for s in range(num_stadiums)) <= 1)

    for d in range(num_days - 2):
        model.Add(sum(matches[(min(t, t2), max(t, t2), s, d)] for t2 in range(num_teams) if t != t2 for s in range(num_stadiums)) +
                  sum(matches[(min(t, t2), max(t, t2), s, d+1)] for t2 in range(num_teams) if t != t2 for s in range(num_stadiums)) +
                  sum(matches[(min(t, t2), max(t, t2), s, d+2)] for t2 in range(num_teams) if t != t2 for s in range(num_stadiums)) <= 2)

# 2. Venue availability
for s in range(num_stadiums):
    for d in range(num_days):
        model.Add(sum(matches[(t1, t2, s, d)] for t1 in range(num_teams) for t2 in range(t1 + 1, num_teams)) <= 1)
        # Simplified to all 1s, so no need to check availability

# 3. Prime time slots
# Assuming all matches are in prime time slots; no additional constraint needed for prime time here.

# 4. Weather conditions
# Assuming matches are not scheduled in regions with seasonal weather disruptions by default.

# 5. Home Matches Constraint
home_stadiums = {
    'Team_1': 'Stadium_1', 'Team_2': 'Stadium_2', 'Team_3': 'Stadium_3', 'Team_4': 'Stadium_4',
    'Team_5': 'Stadium_5', 'Team_6': 'Stadium_6', 'Team_7': 'Stadium_7', 'Team_8': 'Stadium_8',
    'Team_9': 'Stadium_9', 'Team_10': 'Stadium_10', 'Team_11': 'Stadium_1', 'Team_12': 'Stadium_2',
    'Team_13': 'Stadium_3', 'Team_14': 'Stadium_4'
}

for t in range(num_teams):
    home_stadium = stadium_index[home_stadiums[f'Team_{t+1}']]
    model.Add(sum(matches[(min(t, t2), max(t, t2), home_stadium, d)] for t2 in range(num_teams) if t != t2 for d in range(num_days)) == 7)

# 6. Travel Distance Constraint
total_travel_distance = [model.NewIntVar(0, 100000, f'total_travel_distance_{t}') for t in range(num_teams)]
for t in range(num_teams):
    home_stadium = stadium_index[home_stadiums[f'Team_{t+1}']]
    model.Add(total_travel_distance[t] == sum(matches[(min(t, t2), max(t, t2), s, d)] * distance_matrix[home_stadium, s]
                                              for t2 in range(num_teams) if t != t2 for s in range(num_stadiums) for d in range(num_days)))

# Ensure travel distances are approximately equal
total_distance_sum = model.NewIntVar(0, 1000000, 'total_distance_sum')
model.Add(total_distance_sum == sum(total_travel_distance))
average_distance = model.NewIntVar(0, 100000, 'average_distance')
model.AddDivisionEquality(average_distance, total_distance_sum, num_teams)

for t in range(num_teams):
    model.Add(total_travel_distance[t] <= average_distance + 1000)
    model.Add(total_travel_distance[t] >= average_distance - 1000)

# Objective: maximize total number of scheduled matches (secondary to constraints)
objective = sum(matches[(t1, t2, s, d)] for t1 in range(num_teams) for t2 in range(t1 + 1, num_teams) for s in range(num_stadiums) for d in range(num_days))
model.Maximize(objective)

# Solve the model with logging enabled and a time limit
solver = cp_model.CpSolver()
solver.parameters.log_search_progress = True  # Enable logging
solver.parameters.max_time_in_seconds = 300  # Set a time limit of 300 seconds (5 minutes)
status = solver.Solve(model)

# Check solution status and print results
results = []
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    for t1 in range(num_teams):
        for t2 in range(t1 + 1, num_teams):
            for s in range(num_stadiums):
                for d in range(num_days):
                    if solver.Value(matches[(t1, t2, s, d)]):
                        results.append({
                            'Team_1': f'Team_{t1+1}',
                            'Team_2': f'Team_{t2+1}',
                            'Stadium': f'Stadium_{s+1}',
                            'Day': f'Day_{d+1}'
                        })
else:
    print('No feasible solution found.')

results_df = pd.DataFrame(results)
results_df.to_csv('ipl_schedule.csv', index=False)
print(results_df.head())
