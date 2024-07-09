from ortools.sat.python import cp_model
import collections
import random

# Initialize the CP model
model = cp_model.CpModel()

# Simplified data
locations = ["Charanpur Village", "NASA Facility", "Mumbai Studio"]
cast = ["Shah Rukh Khan", "Gayatri Joshi", "Kishori Ballal"]
crew = ["Ashutosh Gowariker", "Mahesh Aney"]
scenes = [f"Scene{i}" for i in range(1, 11)]  # Reduced to 10 scenes
equipment = ["Camera A", "Lighting Set A", "Sound Equipment"]

# Function to generate placeholder data for missing scenes
def generate_placeholder_scene_data():
    return {
        "location": random.choice(locations),
        "cast": random.sample(cast, k=random.randint(1, 2)),
        "crew": random.sample(crew, k=random.randint(1, 2)),
        "duration": random.randint(1, 3),
        "setup_time": 1,
        "daytime": random.choice(["Day", "Night"]),
        "equipment": random.sample(equipment, k=2)
    }

# Existing scene data
scene_data = {
    "Scene1": {"location": "Charanpur Village", "cast": ["Shah Rukh Khan", "Gayatri Joshi"], "crew": ["Ashutosh Gowariker"], "duration": 2, "setup_time": 1, "daytime": "Day", "equipment": ["Camera A", "Lighting Set A"]},
    "Scene2": {"location": "NASA Facility", "cast": ["Shah Rukh Khan"], "crew": ["Ashutosh Gowariker"], "duration": 3, "setup_time": 1, "daytime": "Day", "equipment": ["Camera A", "Sound Equipment"]},
    "Scene3": {"location": "Mumbai Studio", "cast": ["Gayatri Joshi", "Kishori Ballal"], "crew": ["Mahesh Aney"], "duration": 1, "setup_time": 1, "daytime": "Night", "equipment": ["Camera A", "Lighting Set A"]},
}

# Fill in missing scene data with placeholder data
for scene in scenes:
    if scene not in scene_data:
        scene_data[scene] = generate_placeholder_scene_data()

# Simplified constraints
total_days = 30
max_hours_per_day = 12
buffer_time = 0  # Removed buffer time

# Variables
scene_start = {}
scene_end = {}
for scene in scenes:
    scene_start[scene] = model.NewIntVar(1, total_days, f'start_{scene}')
    scene_end[scene] = model.NewIntVar(1, total_days, f'end_{scene}')

# Constraints

# Scene duration
for scene in scenes:
    model.Add(scene_end[scene] == scene_start[scene] + scene_data[scene]["duration"] - 1)

# No overlapping scenes
for i, scene1 in enumerate(scenes):
    for scene2 in scenes[i+1:]:
        scene1_before_scene2 = model.NewBoolVar(f'{scene1}_before_{scene2}')
        model.Add(scene_end[scene1] <= scene_start[scene2]).OnlyEnforceIf(scene1_before_scene2)
        model.Add(scene_end[scene2] <= scene_start[scene1]).OnlyEnforceIf(scene1_before_scene2.Not())

# Maximum working hours per day
for day in range(1, total_days + 1):
    day_scenes = []
    day_durations = []
    for scene in scenes:
        is_on_day = model.NewBoolVar(f'{scene}_on_day_{day}')
        model.Add(scene_start[scene] <= day).OnlyEnforceIf(is_on_day)
        model.Add(day <= scene_end[scene]).OnlyEnforceIf(is_on_day)
        day_scenes.append(is_on_day)
        day_durations.append(scene_data[scene]["duration"])
    model.Add(sum(x * y for x, y in zip(day_scenes, day_durations)) <= max_hours_per_day)

# Objective function
makespan = model.NewIntVar(0, total_days, 'makespan')
model.AddMaxEquality(makespan, [scene_end[scene] for scene in scenes])
model.Minimize(makespan)

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60.0  # Increase solving time to 60 seconds
status = solver.Solve(model)

# Output the schedule
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print("Shooting Schedule:")
    schedule = collections.defaultdict(list)
    for day in range(1, total_days + 1):
        day_scenes = []
        for scene in scenes:
            if solver.Value(scene_start[scene]) <= day <= solver.Value(scene_end[scene]):
                day_scenes.append(scene)
        if day_scenes:
            print(f"Day {day}: {', '.join(day_scenes)}")
            print(f"  Location: {scene_data[day_scenes[0]]['location']}")
            print(f"  Cast: {set.union(*[set(scene_data[s]['cast']) for s in day_scenes])}")
    
    print(f"\nTotal duration: {solver.Value(makespan)} days")
else:
    print("No feasible solution found.")
    print("Solver status:", solver.StatusName(status))
    print("Statistics:")
    print("  - Conflicts:", solver.NumConflicts())
    print("  - Branches :", solver.NumBranches())
    print("  - Wall time:", solver.WallTime(), "seconds")