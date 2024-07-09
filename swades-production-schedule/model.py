from ortools.sat.python import cp_model
import collections
import random

# Initialize the CP model
model = cp_model.CpModel()

# Data
locations = ["Charanpur Village", "NASA Facility", "Mumbai Studio", "Harmandir Sahib", "Wai"]
cast = ["Shah Rukh Khan", "Gayatri Joshi", "Kishori Ballal", "Rajesh Vivek", "Makrand Deshpande"]
crew = ["Ashutosh Gowariker", "Mahesh Aney", "Javed Akhtar", "A. R. Rahman", "Bhanu Athaiya"]
scenes = [f"Scene{i}" for i in range(1, 31)]  # Assuming 30 scenes
equipment = ["Camera A", "Camera B", "Lighting Set A", "Lighting Set B", "Sound Equipment"]

# Function to generate placeholder data for missing scenes


def generate_placeholder_scene_data():
    return {
        "location": random.choice(locations),
        "cast": random.sample(cast, k=random.randint(1, 3)),
        "crew": random.sample(crew, k=random.randint(1, 3)),
        "duration": random.randint(1, 4),
        "setup_time": random.randint(1, 2),
        "daytime": random.choice(["Day", "Night"]),
        "equipment": random.sample(equipment, k=random.randint(2, 3))
    }


# Existing scene data
scene_data = {
    "Scene1": {"location": "Charanpur Village", "cast": ["Shah Rukh Khan", "Gayatri Joshi"], "crew": ["Ashutosh Gowariker", "Mahesh Aney"], "duration": 2, "setup_time": 1, "daytime": "Day", "equipment": ["Camera A", "Lighting Set A", "Sound Equipment"]},
    "Scene2": {"location": "NASA Facility", "cast": ["Shah Rukh Khan"], "crew": ["Ashutosh Gowariker", "Mahesh Aney"], "duration": 3, "setup_time": 2, "daytime": "Day", "equipment": ["Camera B", "Lighting Set B", "Sound Equipment"]},
    "Scene3": {"location": "Mumbai Studio", "cast": ["Gayatri Joshi", "Kishori Ballal"], "crew": ["Ashutosh Gowariker", "Mahesh Aney", "A. R. Rahman"], "duration": 1, "setup_time": 1, "daytime": "Night", "equipment": ["Camera A", "Lighting Set A", "Sound Equipment"]},
    "Scene4": {"location": "Wai", "cast": ["Shah Rukh Khan", "Rajesh Vivek"], "crew": ["Ashutosh Gowariker", "Mahesh Aney", "Bhanu Athaiya"], "duration": 2, "setup_time": 1, "daytime": "Day", "equipment": ["Camera B", "Lighting Set A", "Sound Equipment"]},
    "Scene5": {"location": "Harmandir Sahib", "cast": ["Shah Rukh Khan", "Gayatri Joshi", "Makrand Deshpande"], "crew": ["Ashutosh Gowariker", "Mahesh Aney", "Javed Akhtar"], "duration": 3, "setup_time": 2, "daytime": "Night", "equipment": ["Camera A", "Lighting Set B", "Sound Equipment"]},
}

# Fill in missing scene data with placeholder data
for scene in scenes:
    if scene not in scene_data:
        scene_data[scene] = generate_placeholder_scene_data()

location_availability = {
    "Charanpur Village": list(range(1, 61)),  # Available for 2 months
    "NASA Facility": list(range(30, 45)),     # Available for 2 weeks in the middle
    "Mumbai Studio": list(range(1, 61)),      # Always available
    "Harmandir Sahib": [15, 16, 17, 18, 19],  # Limited availability
    "Wai": list(range(1, 31))                 # Available for the first month
}

cast_availability = {
    "Shah Rukh Khan": list(range(1, 61)),      # Available throughout
    "Gayatri Joshi": list(range(1, 31)) + list(range(45, 61)),  # Break in the middle
    "Kishori Ballal": [i for i in range(1, 61) if i % 3 != 0],  # Available 2 out of every 3 days
    "Rajesh Vivek": list(range(15, 46)),       # Available for a month in the middle
    "Makrand Deshpande": list(range(1, 61, 2))  # Available every other day
}

crew_availability = {
    "Ashutosh Gowariker": list(range(1, 61)),  # Available throughout
    "Mahesh Aney": list(range(1, 61)),         # Available throughout
    "Javed Akhtar": list(range(1, 31)),        # Available for the first month
    "A. R. Rahman": list(range(30, 61)),       # Available for the second month
    "Bhanu Athaiya": list(range(1, 61, 3))     # Available every third day
}

equipment_availability = {eq: list(range(1, 61)) for eq in equipment}  # Assuming all equipment available all days

travel_time = {
    ("Charanpur Village", "NASA Facility"): 2,
    ("Charanpur Village", "Mumbai Studio"): 1,
    ("Charanpur Village", "Harmandir Sahib"): 3,
    ("Charanpur Village", "Wai"): 1,
    ("NASA Facility", "Mumbai Studio"): 2,
    ("NASA Facility", "Harmandir Sahib"): 4,
    ("NASA Facility", "Wai"): 3,
    ("Mumbai Studio", "Harmandir Sahib"): 3,
    ("Mumbai Studio", "Wai"): 1,
    ("Harmandir Sahib", "Wai"): 3
}

weather_forecast = {day: 1 if day % 7 == 0 else 0 for day in range(1, 61)}  # 1 is bad weather, 0 is good weather

scene_priority = {scene: (i % 3) + 1 for i, scene in enumerate(scenes)}  # Priority 1-3
budget_per_day = 50000  # Example budget constraint
scene_cost = {scene: 20000 + 5000 * len(scene_data[scene]["cast"]) for scene in scenes}  # Example cost calculation

max_hours_per_day = 12
total_days = 60
buffer_time = 1

# Variables
scene_start = {}
scene_end = {}
for scene in scenes:
    scene_start[scene] = model.NewIntVar(1, total_days, f'start_{scene}')
    scene_end[scene] = model.NewIntVar(1, total_days, f'end_{scene}')

equipment_use = {(eq, day): model.NewBoolVar(f'{eq}_used_day_{day}')
                 for eq in equipment for day in range(1, total_days + 1)}
daily_cost = {day: model.NewIntVar(0, budget_per_day, f'cost_day_{day}') for day in range(1, total_days + 1)}

# Constraints

# Scene duration and setup time
for scene in scenes:
    model.Add(scene_end[scene] == scene_start[scene] + scene_data[scene]
              ["duration"] + scene_data[scene]["setup_time"] - 1)

# Location availability
for scene in scenes:
    location = scene_data[scene]["location"]
    model.AddAllowedAssignments([scene_start[scene]], [(day,) for day in location_availability[location]])

# Cast and crew availability
for scene in scenes:
    for actor in scene_data[scene]["cast"]:
        model.AddAllowedAssignments([scene_start[scene]], [(day,) for day in cast_availability[actor]])
    for crew_member in scene_data[scene]["crew"]:
        model.AddAllowedAssignments([scene_start[scene]], [(day,) for day in crew_availability[crew_member]])

# No overlapping scenes
for i, scene1 in enumerate(scenes):
    for scene2 in scenes[i+1:]:
        scene1_before_scene2 = model.NewBoolVar(f'{scene1}_before_{scene2}')
        model.Add(scene_start[scene1] < scene_start[scene2]).OnlyEnforceIf(scene1_before_scene2)
        model.Add(scene_start[scene2] <= scene_start[scene1]).OnlyEnforceIf(scene1_before_scene2.Not())

        model.Add(scene_end[scene1] <= scene_start[scene2]).OnlyEnforceIf(scene1_before_scene2)
        model.Add(scene_end[scene2] <= scene_start[scene1]).OnlyEnforceIf(scene1_before_scene2.Not())

# Travel time between locations
for i, scene1 in enumerate(scenes):
    for scene2 in scenes[i+1:]:
        loc1, loc2 = scene_data[scene1]["location"], scene_data[scene2]["location"]
        if loc1 != loc2:
            travel = travel_time.get((loc1, loc2), travel_time.get((loc2, loc1), 0))
            scene1_before_scene2 = model.NewBoolVar(f'{scene1}_before_{scene2}_travel')
            model.Add(scene_start[scene1] < scene_start[scene2]).OnlyEnforceIf(scene1_before_scene2)
            model.Add(scene_start[scene2] <= scene_start[scene1]).OnlyEnforceIf(scene1_before_scene2.Not())

            model.Add(scene_start[scene2] >= scene_end[scene1] + travel).OnlyEnforceIf(scene1_before_scene2)
            model.Add(scene_start[scene1] >= scene_end[scene2] + travel).OnlyEnforceIf(scene1_before_scene2.Not())

# Weather constraints for outdoor scenes
for scene in scenes:
    if scene_data[scene]["location"] not in ["Mumbai Studio"]:  # Assuming all except Mumbai Studio are outdoor
        for day in range(1, total_days + 1):
            model.Add(scene_start[scene] != day).OnlyEnforceIf(model.NewBoolVar(f'{scene}_not_on_bad_weather_{day}'))
            model.Add(weather_forecast[day] == 1).OnlyEnforceIf(model.NewBoolVar(f'{scene}_not_on_bad_weather_{day}'))

# Buffer time between scenes
for i, scene1 in enumerate(scenes):
    for scene2 in scenes[i+1:]:
        scene1_before_scene2 = model.NewBoolVar(f'{scene1}_before_{scene2}_buffer')
        model.Add(scene_start[scene1] < scene_start[scene2]).OnlyEnforceIf(scene1_before_scene2)
        model.Add(scene_start[scene2] <= scene_start[scene1]).OnlyEnforceIf(scene1_before_scene2.Not())

        model.Add(scene_start[scene2] >= scene_end[scene1] + buffer_time).OnlyEnforceIf(scene1_before_scene2)
        model.Add(scene_start[scene1] >= scene_end[scene2] + buffer_time).OnlyEnforceIf(scene1_before_scene2.Not())

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

# Equipment availability constraint
for scene in scenes:
    for eq in scene_data[scene]["equipment"]:
        for day in range(1, total_days + 1):
            is_scene_on_day = model.NewBoolVar(f'{scene}_uses_{eq}_on_day_{day}')
            model.Add(scene_start[scene] <= day).OnlyEnforceIf(is_scene_on_day)
            model.Add(day <= scene_end[scene]).OnlyEnforceIf(is_scene_on_day)
            model.Add(equipment_use[(eq, day)] == 1).OnlyEnforceIf(is_scene_on_day)

# Budget constraint
for day in range(1, total_days + 1):
    scene_costs_today = []
    for scene in scenes:
        is_scene_today = model.NewBoolVar(f'{scene}_on_day_{day}')
        model.Add(scene_start[scene] <= day).OnlyEnforceIf(is_scene_today)
        model.Add(day <= scene_end[scene]).OnlyEnforceIf(is_scene_today)
        scene_costs_today.append(model.NewIntVar(0, scene_cost[scene], f'{scene}_cost_day_{day}'))
        model.Add(scene_costs_today[-1] == scene_cost[scene]).OnlyEnforceIf(is_scene_today)
        model.Add(scene_costs_today[-1] == 0).OnlyEnforceIf(is_scene_today.Not())
    model.Add(sum(scene_costs_today) == daily_cost[day])
    model.Add(daily_cost[day] <= budget_per_day)

# Objective function
makespan = model.NewIntVar(0, total_days, 'makespan')
model.AddMaxEquality(makespan, [scene_end[scene] for scene in scenes])

total_cost = sum(daily_cost.values())

total_cost = sum(daily_cost.values())

# Multi-objective optimization
alpha = 0.7  # Weight for duration vs. cost (adjust as needed)
beta = 0.1   # Weight for scene priority (adjust as needed)


# Create variables for priority-weighted start times
priority_weighted_starts = {}
for scene in scenes:
    priority_weighted_starts[scene] = model.NewIntVar(0, scene_priority[scene] * total_days, f'priority_weighted_start_{scene}')
    model.Add(priority_weighted_starts[scene] == scene_priority[scene] * (total_days - scene_start[scene]))

priority_sum = sum(priority_weighted_starts.values())

# Objective: Minimize weighted sum of makespan, total cost, and negative priority sum
model.Minimize(alpha * makespan + (1 - alpha) * total_cost - beta * priority_sum)

# Solve
solver = cp_model.CpSolver()
status = solver.Solve(model)

# Output the schedule
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print("Shooting Schedule:")
    schedule = collections.defaultdict(list)
    total_budget_used = 0
    for day in range(1, total_days + 1):
        day_scenes = []
        day_cost = solver.Value(daily_cost[day])
        total_budget_used += day_cost
        for scene in scenes:
            if solver.Value(scene_start[scene]) <= day <= solver.Value(scene_end[scene]):
                day_scenes.append(scene)
        if day_scenes:
            print(f"Day {day}: {', '.join(day_scenes)} (Cost: ${day_cost})")
            print(f"  Location: {scene_data[day_scenes[0]]['location']}")
            print(f"  Cast: {set.union(*[set(scene_data[s]['cast']) for s in day_scenes])}")
            print(f"  Equipment: {[eq for eq in equipment if solver.Value(equipment_use[(eq, day)]) == 1]}")

    print(f"\nTotal duration: {solver.Value(makespan)} days")
    print(f"Total budget used: ${total_budget_used}")
else:
    print("No feasible solution found.")
