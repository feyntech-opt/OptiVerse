from ortools.sat.python import cp_model
import collections
import random

# Initialize the CP model
model = cp_model.CpModel()

# Data (keeping the same as before)
locations = ["Charanpur Village", "NASA Facility", "Mumbai Studio", "Harmandir Sahib", "Wai"]
cast = ["Shah Rukh Khan", "Gayatri Joshi", "Kishori Ballal", "Rajesh Vivek", "Makrand Deshpande"]
crew = ["Ashutosh Gowariker", "Mahesh Aney", "Javed Akhtar", "A. R. Rahman", "Bhanu Athaiya"]
scenes = [f"Scene{i}" for i in range(1, 16)]  # Keeping 15 scenes
equipment = ["Camera A", "Camera B", "Lighting Set A", "Lighting Set B", "Sound Equipment"]

# Scene data generation function (adjusted for half-day units)
def generate_placeholder_scene_data():
    return {
        "location": random.choice(locations),
        "cast": random.sample(cast, k=random.randint(1, 3)),
        "crew": random.sample(crew, k=random.randint(1, 3)),
        "duration": random.randint(2, 6),  # 1-3 days in half-day units
        "setup_time": 2,  # 1 day in half-day units
        "daytime": random.choice(["Day", "Night"]),
        "equipment": random.sample(equipment, k=2)
    }

# Scene data (adjusted for half-day units)
scene_data = {
    "Scene1": {"location": "Charanpur Village", "cast": ["Shah Rukh Khan", "Gayatri Joshi"], "crew": ["Ashutosh Gowariker", "Mahesh Aney"], "duration": 4, "setup_time": 2, "daytime": "Day", "equipment": ["Camera A", "Lighting Set A"]},
    "Scene2": {"location": "NASA Facility", "cast": ["Shah Rukh Khan"], "crew": ["Ashutosh Gowariker", "Mahesh Aney"], "duration": 6, "setup_time": 2, "daytime": "Day", "equipment": ["Camera B", "Sound Equipment"]},
    "Scene3": {"location": "Mumbai Studio", "cast": ["Gayatri Joshi", "Kishori Ballal"], "crew": ["Ashutosh Gowariker", "Mahesh Aney"], "duration": 2, "setup_time": 2, "daytime": "Night", "equipment": ["Camera A", "Lighting Set A"]},
    "Scene4": {"location": "Wai", "cast": ["Shah Rukh Khan", "Rajesh Vivek"], "crew": ["Ashutosh Gowariker", "Mahesh Aney"], "duration": 4, "setup_time": 2, "daytime": "Day", "equipment": ["Camera B", "Lighting Set A"]},
    "Scene5": {"location": "Harmandir Sahib", "cast": ["Shah Rukh Khan", "Gayatri Joshi"], "crew": ["Ashutosh Gowariker", "Mahesh Aney"], "duration": 6, "setup_time": 2, "daytime": "Night", "equipment": ["Camera A", "Lighting Set B"]},
}

for scene in scenes:
    if scene not in scene_data:
        scene_data[scene] = generate_placeholder_scene_data()

# Constraints
total_half_days = 90  # 45 days in half-day units
max_hours_per_half_day = 1  # Only one scene per half-day
buffer_time = 1  # 0.5 days in half-day units

# Variables
scene_start = {}
scene_end = {}
scene_buffer = {}
for scene in scenes:
    scene_start[scene] = model.NewIntVar(1, total_half_days, f'start_{scene}')
    scene_end[scene] = model.NewIntVar(1, total_half_days, f'end_{scene}')
    scene_buffer[scene] = model.NewIntVar(0, buffer_time, f'buffer_{scene}')

# Constraints

# Scene duration and setup time
for scene in scenes:
    model.Add(scene_end[scene] == scene_start[scene] + scene_data[scene]["duration"] + scene_data[scene]["setup_time"] - 1)

# No overlapping scenes with buffer time
for i, scene1 in enumerate(scenes):
    for scene2 in scenes[i+1:]:
        scene1_before_scene2 = model.NewBoolVar(f'{scene1}_before_{scene2}')
        model.Add(scene_end[scene1] + scene_buffer[scene1] <= scene_start[scene2]).OnlyEnforceIf(scene1_before_scene2)
        model.Add(scene_end[scene2] + scene_buffer[scene2] <= scene_start[scene1]).OnlyEnforceIf(scene1_before_scene2.Not())

# Maximum working hours per half-day
for half_day in range(1, total_half_days + 1):
    half_day_scenes = []
    for scene in scenes:
        is_on_half_day = model.NewBoolVar(f'{scene}_on_half_day_{half_day}')
        model.Add(scene_start[scene] <= half_day).OnlyEnforceIf(is_on_half_day)
        model.Add(half_day <= scene_end[scene]).OnlyEnforceIf(is_on_half_day)
        half_day_scenes.append(is_on_half_day)
    model.Add(sum(half_day_scenes) <= max_hours_per_half_day)

# Objective function
makespan = model.NewIntVar(0, total_half_days, 'makespan')
model.AddMaxEquality(makespan, [scene_end[scene] + scene_buffer[scene] for scene in scenes])
model.Minimize(makespan)

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 300.0  # Keeping 5 minutes
status = solver.Solve(model)

# Output the schedule
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print("Shooting Schedule:")
    schedule = collections.defaultdict(list)
    for half_day in range(1, total_half_days + 1):
        half_day_scenes = []
        for scene in scenes:
            if solver.Value(scene_start[scene]) <= half_day <= solver.Value(scene_end[scene]):
                half_day_scenes.append(scene)
        if half_day_scenes:
            print(f"Day {(half_day+1)//2}, {'Morning' if half_day % 2 == 1 else 'Afternoon'}: {', '.join(half_day_scenes)}")
            print(f"  Location: {scene_data[half_day_scenes[0]]['location']}")
            print(f"  Cast: {set.union(*[set(scene_data[s]['cast']) for s in half_day_scenes])}")
    
    print(f"\nTotal duration: {(solver.Value(makespan)+1)//2} days")
else:
    print("No feasible solution found.")
    print("Solver status:", solver.StatusName(status))
    print("Statistics:")
    print("  - Conflicts:", solver.NumConflicts())
    print("  - Branches :", solver.NumBranches())
    print("  - Wall time:", solver.WallTime(), "seconds")

    # Additional debugging information
    print("\nScene Data:")
    for scene, data in scene_data.items():
        print(f"{scene}: Duration: {data['duration']/2} days, Setup: {data['setup_time']/2} days, Location: {data['location']}, Cast: {data['cast']}")

    print("\nTotal scene time:", sum(data['duration'] + data['setup_time'] for data in scene_data.values()) / 2, "days")
    print("Available time:", total_half_days / 2, "days")