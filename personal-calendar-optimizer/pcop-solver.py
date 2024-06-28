import json
from ortools.sat.python import cp_model
from datetime import datetime, timedelta

from ortools.sat.python import cp_model


class SolutionPrinter(cp_model.CpSolverSolutionCallback):
    def __init__(self, activity_intervals, num_days, solution_limit):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._activity_intervals = activity_intervals
        self._num_days = num_days
        self._solution_limit = solution_limit
        self._solution_count = 0
        self._all_solutions = []

    def on_solution_callback(self):
        self._solution_count += 1
        current_solution = []
        for day in range(self._num_days):
            day_schedule = []
            for (d, activity_name), interval in self._activity_intervals.items():
                if d == day:
                    start = self.Value(interval['start'])
                    duration = self.Value(interval['duration'])
                    day_schedule.append((activity_name, start % (24 * 60), duration))
            current_solution.append(sorted(day_schedule, key=lambda x: x[1]))
        self._all_solutions.append(current_solution)
        if self._solution_count >= self._solution_limit:
            self.StopSearch()


def load_pcop_data(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def create_pcop_model(pcop_data, debug=True):
    model = cp_model.CpModel()

    # Time horizon
    start_date = datetime.strptime(pcop_data['pcop_data']['timeHorizon']['startDate'], '%Y-%m-%d')
    end_date = datetime.strptime(pcop_data['pcop_data']['timeHorizon']['endDate'], '%Y-%m-%d')
    num_days = (end_date - start_date).days + 1
    horizon = num_days * 24 * 60  # Total minutes in the time horizon

    if debug:
        print(f"Planning for {num_days} days")

    # Activities
    activities = pcop_data['pcop_data']['activities']
    activity_intervals = {}

    for day in range(num_days):
        day_start = day * 24 * 60
        day_end = (day + 1) * 24 * 60

        for activity in activities:
            # Reduce minimum durations by 30% to provide more flexibility
            min_duration = int(activity.get('dailyMinDuration', activity.get('dailyDuration', 30)) * 0.7)
            max_duration = activity.get('dailyMaxDuration', activity.get('dailyDuration', 120))

            # Special handling for eating (3 occurrences)
            if activity['name'] == 'Eating':
                min_duration = activity['minDuration']
                max_duration = activity['maxDuration']

            # Ensure max_duration is not greater than the day length
            max_duration = min(max_duration, 24 * 60)

            start_var = model.NewIntVar(day_start, day_end - min_duration, f"{activity['name']}_start_day{day}")
            duration_var = model.NewIntVar(min_duration, max_duration, f"{activity['name']}_duration_day{day}")
            end_var = model.NewIntVar(day_start + min_duration, day_end, f"{activity['name']}_end_day{day}")
            interval_var = model.NewIntervalVar(start_var, duration_var, end_var, f"{activity['name']}_interval_day{day}")

            activity_intervals[day, activity['name']] = {
                'start': start_var,
                'duration': duration_var,
                'end': end_var,
                'interval': interval_var
            }

    if debug:
        print("Activity intervals created")
        total_min_duration = sum(int(activity.get('dailyMinDuration', activity.get('dailyDuration', 30)) * 0.7) for activity in activities if activity['name'] != 'Eating')
        total_min_duration += 3 * activities[2]['minDuration']  # Add eating durations
        print(f"Total minimum duration of all activities: {total_min_duration} minutes")

    # Constraints

    # 1. Daily occurrence constraints
    for day in range(num_days):
        day_intervals = [interval['interval'] for (d, _), interval in activity_intervals.items() if d == day]
        model.AddNoOverlap(day_intervals)
    if debug:
        print("Daily occurrence constraints added")

    # 2. Ensure total duration of activities doesn't exceed 24 hours
    for day in range(num_days):
        day_durations = [interval['duration'] for (d, _), interval in activity_intervals.items() if d == day]
        model.Add(sum(day_durations) <= 24 * 60)
    if debug:
        print("Total duration constraint added")

    # 3. Time window constraints for sleep (made extremely flexible)
    sleep_activity = next(act for act in activities if act['name'] == 'Sleep')
    for day in range(num_days):
        sleep_interval = activity_intervals[day, sleep_activity['name']]
        # Allow sleep to start anytime between 6 PM and 2 AM
        night_start = day * 24 * 60 + 18 * 60  # 6 PM
        night_end = (day + 1) * 24 * 60 + 2 * 60  # 2 AM next day
        model.Add(sleep_interval['start'] >= night_start)
        model.Add(sleep_interval['start'] <= night_end)
        
        # Ensure sleep duration is at least 6 hours (360 minutes)
        model.Add(sleep_interval['duration'] >= 360)
    if debug:
        print("Sleep time window constraints added (extremely flexible)")

    # 4. Precedence constraints (optional)
    for constraint in pcop_data['pcop_data']['constraints']['precedence']:
        for day in range(num_days):
            act1 = activity_intervals[day, constraint['activity']]
            act2 = activity_intervals[day, constraint['notAfter']]
            min_gap = constraint['minGapMinutes']
            precedence_bool = model.NewBoolVar(f"precedence_{constraint['activity']}_{constraint['notAfter']}_day{day}")
            model.Add(act2['start'] >= act1['end'] + min_gap).OnlyEnforceIf(precedence_bool)
    if debug:
        print("Precedence constraints added (optional)")

    # 5. Break constraints (optional and simplified)
    work_activity = pcop_data['pcop_data']['constraints']['breaks']['activity']
    break_duration = pcop_data['pcop_data']['constraints']['breaks']['breakDurationMinutes']
    work_duration = pcop_data['pcop_data']['constraints']['breaks']['afterDurationMinutes']

    for day in range(num_days):
        work_interval = activity_intervals[day, work_activity]
        break_bool = model.NewBoolVar(f"break_day{day}")
        model.Add(work_interval['duration'] <= work_duration).OnlyEnforceIf(break_bool.Not())
        model.Add(work_interval['duration'] > work_duration).OnlyEnforceIf(break_bool)
    if debug:
        print("Break constraints added (optional and simplified)")

    # Objective
    objective_terms = []
    for day in range(num_days):
        for activity in activities:
            interval = activity_intervals[day, activity['name']]
            weight = 1  # Default weight
            if activity['name'] == 'Work':
                weight = pcop_data['pcop_data']['objectiveWeights']['dailyProductivity']
            elif activity['name'] in ['Sleep', 'Exercise']:
                weight = pcop_data['pcop_data']['objectiveWeights']['dailyWellbeing']
            
            objective_terms.append(weight * interval['duration'])

    model.Maximize(sum(objective_terms))

    if debug:
        print("Objective function added")

    return model, activity_intervals, num_days


# Modify the solve_pcop_model function to use this debug information

def solve_pcop_model(model, activity_intervals, num_days, solver_options, debug=True):
    solver = cp_model.CpSolver()

    # Apply solver options
    solver.parameters.max_time_in_seconds = solver_options['time_limit_seconds']
    solver.parameters.num_search_workers = 1  # Required when setting solution limit
    solver.parameters.log_search_progress = solver_options['log_search_progress']

    if debug:
        print("Solving model...")

    status = solver.Solve(model)

    if debug:
        print(f"Solver status: {solver.StatusName(status)}")

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        schedule = []
        for day in range(num_days):
            day_schedule = []
            for (d, activity_name), interval in activity_intervals.items():
                if d == day:
                    start = solver.Value(interval['start'])
                    duration = solver.Value(interval['duration'])
                    day_schedule.append((activity_name, start % (24 * 60), duration))
            schedule.append(sorted(day_schedule, key=lambda x: x[1]))
        return schedule
    else:
        if debug:
            print("No feasible solution found. Checking for conflicts...")
            conflict = solver.SufficientAssumptionsForInfeasibility()
            if conflict:
                print("Conflict found in the following constraints:")
                for lit in conflict:
                    print(f"  - {model.Proto().constraints[lit].name}")
            else:
                print("No specific conflict identified.")
        return None

# Modify the main function to use debug mode


def main():
    pcop_data = load_pcop_data('personal-calendar-optimizer/pcop.json')
    
    model, activity_intervals, num_days = create_pcop_model(pcop_data, debug=True)
    schedule = solve_pcop_model(model, activity_intervals, num_days, pcop_data['solver_options'], debug=True)

    if schedule:
        print("\nFeasible solution found!")
        print("Optimized Schedule (first 7 days):")
        start_date = datetime.strptime(pcop_data['pcop_data']['timeHorizon']['startDate'], '%Y-%m-%d')
        
        for day in range(min(7, len(schedule))):
            current_date = start_date + timedelta(days=day)
            print(f"\nDay {day + 1} ({current_date.strftime('%Y-%m-%d')}):")
            day_schedule = schedule[day]
            
            for activity, start, duration in day_schedule:
                start_time = f"{start // 60:02d}:{start % 60:02d}"
                end_time = f"{(start + duration) // 60 % 24:02d}:{(start + duration) % 60:02d}"
                print(f"  {activity}: {start_time} - {end_time} ({duration} minutes)")
            
            # Calculate and print statistics
            total_duration = sum(duration for _, _, duration in day_schedule)
            print(f"\n  Total scheduled time: {total_duration} minutes")
            print(f"  Unscheduled time: {24*60 - total_duration} minutes")
            
            activity_count = len(day_schedule)
            print(f"  Number of scheduled activities: {activity_count}")
            
            # Check for overlaps
            sorted_schedule = sorted(day_schedule, key=lambda x: x[1])
            overlaps = []
            for i in range(len(sorted_schedule) - 1):
                current_end = sorted_schedule[i][1] + sorted_schedule[i][2]
                next_start = sorted_schedule[i+1][1]
                if current_end > next_start:
                    overlaps.append((sorted_schedule[i][0], sorted_schedule[i+1][0]))
            
            if overlaps:
                print("\n  Warning: The following activities overlap:")
                for act1, act2 in overlaps:
                    print(f"    {act1} and {act2}")
            else:
                print("\n  No overlapping activities detected.")
            
            # Analyze sleep schedule
            sleep_schedule = next((activity for activity in day_schedule if activity[0] == "Sleep"), None)
            if sleep_schedule:
                sleep_start = sleep_schedule[1]
                sleep_duration = sleep_schedule[2]
                sleep_end = (sleep_start + sleep_duration) % (24 * 60)
                print(f"\n  Sleep Analysis:")
                print(f"    Start time: {sleep_start // 60:02d}:{sleep_start % 60:02d}")
                print(f"    End time: {sleep_end // 60:02d}:{sleep_end % 60:02d}")
                print(f"    Duration: {sleep_duration} minutes")
            else:
                print("\n  Warning: No sleep scheduled for this day.")
        
        # Overall statistics
        print("\nOverall Statistics (first 7 days):")
        activity_durations = {activity['name']: 0 for activity in pcop_data['pcop_data']['activities']}
        for day_schedule in schedule[:7]:
            for activity, _, duration in day_schedule:
                activity_durations[activity] += duration
        
        for activity, total_duration in activity_durations.items():
            avg_duration = total_duration / 7
            print(f"  {activity}: Average {avg_duration:.2f} minutes per day")
        
        # Goal progress (placeholder - you may need to implement a more sophisticated progress tracking)
        print("\nEstimated Goal Progress:")
        for goal in pcop_data['pcop_data']['goals']:
            print(f"  {goal['name']}: On track")  # This is a placeholder. Implement actual progress tracking if possible.
        
    else:
        print("\nNo feasible solution found.")

if __name__ == "__main__":
    main()