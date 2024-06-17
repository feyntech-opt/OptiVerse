import pandas as pd
from ortools.sat.python import cp_model
import json
from collections import defaultdict

# Load data
teams_home_df = pd.read_csv('ipl-scheduling/teams_home.csv')
venues_df = pd.read_csv('ipl-scheduling/venues.csv')
distance_df = pd.read_csv('ipl-scheduling/distance_matrix.csv', index_col=0)

# Load rules
with open('ipl-scheduling/ipl_rules.json', 'r') as f:
    rules = json.load(f)

# Parameters
num_days = rules['num_days']
home_matches_per_team = rules['home_matches_per_team']
rest_days_between_matches = rules['rest_days_between_matches']
max_matches_per_day = rules['max_matches_per_day']


teams = teams_home_df['Team'].tolist()
num_teams = len(teams)
num_stadiums = len(venues_df)

# Create team and stadium mappings
team_index = {team: i for i, team in enumerate(teams)}
stadium_index = {row['Stadium']: i for i, row in venues_df.iterrows()}
home_stadiums = {team_index[row['Team']]: stadium_index[row['Home_Stadium']] for i, row in teams_home_df.iterrows()}


# Create team name to index mapping
team_name_to_index = {team: i for i, team in enumerate(teams)}

group_a = [team_name_to_index[team] for team in rules['groups']['group_a']]
group_b = [team_name_to_index[team] for team in rules['groups']['group_b']]

# Define model
model = cp_model.CpModel()

# Variables and Constraints
matches = {}
team_availability = defaultdict(list)
venue_availability = defaultdict(list)
home_matches = defaultdict(list)
group_stage_constraints = defaultdict(list)
inter_group_constraints = defaultdict(list)
travel_distance_constraints = defaultdict(list)

total_travel_distance = [model.NewIntVar(0, 100000, f'total_travel_distance_{t}') for t in range(num_teams)]

distance_matrix = distance_df.values

for t1 in range(num_teams):
    for t2 in range(t1 + 1, num_teams):
        for s in range(num_stadiums):
            for d in range(num_days):
                matches[(min(t1, t2), max(t1, t2), s, d)] = model.NewBoolVar(f'match_{t1}_{t2}_{s}_{d}')
                
                # Team availability constraints
                team_availability[t1, d].append(matches[(min(t1, t2), max(t1, t2), s, d)])
                team_availability[t2, d].append(matches[(min(t1, t2), max(t1, t2), s, d)])
                
                # Rest days between matches
                for r in range(rest_days_between_matches):
                    if d + r < num_days:
                        team_availability[t1, d + r].append(matches[(min(t1, t2), max(t1, t2), s, d)])
                        team_availability[t2, d + r].append(matches[(min(t1, t2), max(t1, t2), s, d)])
                
                # Venue availability constraints
                venue_availability[s, d].append(matches[(min(t1, t2), max(t1, t2), s, d)])
                
                # Home matches constraints
                if s == home_stadiums[t1]:
                    home_matches[t1].append(matches[(min(t1, t2), max(t1, t2), s, d)])
                if s == home_stadiums[t2]:
                    home_matches[t2].append(matches[(min(t1, t2), max(t1, t2), s, d)])
                
                # Travel distance constraints
                travel_distance_constraints[t1].append(matches[(min(t1, t2), max(t1, t2), s, d)] * distance_matrix[home_stadiums[t1], s])
                travel_distance_constraints[t2].append(matches[(min(t1, t2), max(t1, t2), s, d)] * distance_matrix[home_stadiums[t2], s])

for (t, d), match_vars in team_availability.items():
    model.Add(sum(match_vars) <= max_matches_per_day)

for (s, d), match_vars in venue_availability.items():
    model.Add(sum(match_vars) <= max_matches_per_day)

for t, match_vars in home_matches.items():
    model.Add(sum(match_vars) == home_matches_per_team)

# Matches within the same group
for group in [group_a, group_b]:
    for i, t1 in enumerate(group):
        for j, t2 in enumerate(group):
            if i < j:
                match_vars = [matches[(min(t1, t2), max(t1, t2), s, d)] for s in range(num_stadiums) for d in range(num_days) if (min(t1, t2), max(t1, t2), s, d) in matches]
                if match_vars:
                    model.Add(sum(match_vars) == 2)

# Matches against the team in the same row in the other group
for i in range(len(group_a)):
    t1 = group_a[i]
    t2 = group_b[i]
    match_vars = [matches[(min(t1, t2), max(t1, t2), s, d)] for s in range(num_stadiums) for d in range(num_days) if (min(t1, t2), max(t1, t2), s, d) in matches]
    if match_vars:
        model.Add(sum(match_vars) == 1)

# Matches against the remaining four teams in the other group
for t1 in group_a:
    remaining_teams = [t for t in group_b if t != group_b[group_a.index(t1)]]
    for t2 in remaining_teams:
        match_vars = [matches[(min(t1, t2), max(t1, t2), s, d)] for s in range(num_stadiums) for d in range(num_days) if (min(t1, t2), max(t1, t2), s, d) in matches]
        if match_vars:
            model.Add(sum(match_vars) == 1)

for t1 in group_b:
    remaining_teams = [t for t in group_a if t != group_a[group_b.index(t1)]]
    for t2 in remaining_teams:
        match_vars = [matches[(min(t1, t2), max(t1, t2), s, d)] for s in range(num_stadiums) for d in range(num_days) if (min(t1, t2), max(t1, t2), s, d) in matches]
        if match_vars:
            model.Add(sum(match_vars) == 1)

for t, match_vars in travel_distance_constraints.items():
    model.Add(total_travel_distance[t] == sum(match_vars))


total_distance_sum = model.NewIntVar(0, 1000000, 'total_distance_sum')
model.Add(total_distance_sum == sum(total_travel_distance))
average_distance = model.NewIntVar(0, 100000, 'average_distance')
# model.AddDivisionEquality(average_distance, total_distance_sum, num_teams)
# for t in range(num_teams):
#     model.Add(total_travel_distance[t] <= average_distance + 1000)
#     model.Add(total_travel_distance[t] >= average_distance - 1000)

# Objective
model.Minimize(total_distance_sum)

# Solve
solver = cp_model.CpSolver()
solver.parameters.log_search_progress = True
solver.parameters.max_time_in_seconds = 300
status = solver.Solve(model)

# Output results
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    print("Schedule found!")
    schedule = []
    for t1 in range(num_teams):
        for t2 in range(t1 + 1, num_teams):
            for s in range(num_stadiums):
                for d in range(num_days):
                    if solver.BooleanValue(matches[(t1, t2, s, d)]):
                        schedule.append([teams[t1], teams[t2], venues_df.iloc[s]['Stadium'], d])
    schedule_df = pd.DataFrame(schedule, columns=['Team1', 'Team2', 'Stadium', 'Day'])
    schedule_df.to_csv('ipl_schedule.csv', index=False)
else:
    print("No feasible solution found.")