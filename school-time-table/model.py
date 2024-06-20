import json
import csv
from ortools.sat.python import cp_model

# Load the JSON data
with open('school-time-table/input_data.json') as f:
    data = json.load(f)

# Extract data
days = list(data['class_schedule'].keys())
periods_per_day = data['periods_per_day']
subjects = list(set(subject for day in days for subject in data['class_schedule'][day]))
teachers = data['teachers']

# Create model
model = cp_model.CpModel()

# Variables
assignments = {}
for day in days:
    for period in range(periods_per_day[day]):
        for teacher in teachers:
            for subject in teacher['subjects']:
                assignments[(day, period, subject, teacher['name'])] = model.NewBoolVar(
                    f'assign_{day}_{period}_{subject}_{teacher["name"]}')

# Constraints
# # Each period must have exactly one subject assigned, taught by an available teacher
for day in days:
    for period in range(periods_per_day[day]):
        model.Add(sum(assignments[(day, period, subject, teacher['name'])]
                  for teacher in teachers for subject in teacher['subjects'] if teacher['availability'][day][period]) == 1)

# Ensure teachers' availability
for teacher in teachers:
    for day in days:
        for period in range(periods_per_day[day]):
            for subject in teacher['subjects']:
                if not teacher['availability'][day][period]:
                    model.Add(assignments[(day, period, subject, teacher['name'])] == 0)

# Ensure each subject is assigned at most once per day
for day in days:
    for subject in subjects:
        model.Add(sum(assignments[(day, period, subject, teacher['name'])] for period in range(periods_per_day[day])
                  for teacher in teachers if subject in teacher['subjects'] and teacher['availability'][day][period]) <= 2)

# Ensure consecutive assignments of the same subject on the same day are handled by the same teacher
for day in days:
    for subject in subjects:
        for period in range(periods_per_day[day] - 1):
            for teacher1 in teachers:
                if subject in teacher1['subjects']:
                    for teacher2 in teachers:
                        if teacher1 != teacher2:
                            if subject in teacher2['subjects']:
                                model.Add(assignments[(day, period, subject, teacher1['name'])] +
                                          assignments[(day, period + 1, subject, teacher2['name'])] <= 1)

# Ensure each subject is assigned the required number of periods per week
for subject, required_periods in data['subject_periods'].items():
    model.Add(sum(assignments[(day, period, subject, teacher['name'])] for day in days for period in range(periods_per_day[day])
              for teacher in teachers if subject in teacher['subjects'] and teacher['availability'][day][period]) == required_periods)

# # Ensure teachers' workloads are balanced within a range
# total_periods = sum(periods_per_day[day] for day in days)
# average_workload = total_periods * len(subjects) // len(teachers)
# min_workload = average_workload - 20
# max_workload = average_workload + 20

# for teacher in teachers:
#     model.AddLinearConstraint(
#         sum(assignments[(day, period, subject, teacher['name'])]
#             for day in days for period in range(periods_per_day[day]) for subject in teacher['subjects']),
#         min_workload,
#         max_workload
    # )

# # Seniority preference
# for subject in subjects:
#     senior_teachers = sorted(teachers, key=lambda t: -t["seniority_level"])
#     for day in days:
#         for period in range(periods_per_day[day]):
#             for i, senior_teacher in enumerate(senior_teachers):
#                 if subject in senior_teacher['subjects']:
#                     for junior_teacher in senior_teachers[i+1:]:
#                         if subject in junior_teacher['subjects']:
#                             model.Add(assignments[(day, period, subject, senior_teacher['name'])] >= assignments[(day, period, subject, junior_teacher['name'])])

# Solver
solver = cp_model.CpSolver()
solver.parameters.log_search_progress = True
solver.parameters.max_time_in_seconds = 10


class SolutionPrinter(cp_model.CpSolverSolutionCallback):
    def __init__(self, assignments, limit=3):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.assignments = assignments
        self.solution_count = 0
        self.solutions = []
        self.limit = limit

    def OnSolutionCallback(self):
        if self.solution_count >= self.limit:
            return
        self.solution_count += 1
        solution = {'solution_number': self.solution_count}
        for day in days:
            solution[day] = []
            for period in range(periods_per_day[day]):
                for teacher in teachers:
                    for subject in teacher['subjects']:
                        if self.Value(assignments[(day, period, subject, teacher['name'])]):
                            solution[day].append({"period": period + 1, "subject": subject, "teacher": teacher['name']})
        self.solutions.append(solution)


# Instantiate and solve the model with the solution printer
solution_printer = SolutionPrinter(assignments, limit=3)
solver.SearchForAllSolutions(model, solution_printer)

# Save solutions to JSON with solution number
with open('school-time-table/solutions.json', 'w') as f:
    json.dump(solution_printer.solutions, f, indent=4)

print(f'Number of solutions found: {solution_printer.solution_count}')

# Generate CSV calendar for each solution
for solution in solution_printer.solutions:
    csv_filename = f'school-time-table/calendar_solution_{solution["solution_number"]}.csv'
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['Period'] + days
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        max_periods = max(periods_per_day.values())
        for period in range(1, max_periods + 1):
            row = {'Period': period}
            for day in days:
                if period <= periods_per_day[day]:
                    assignment = next((a for a in solution[day] if a['period'] == period), None)
                    if assignment:
                        row[day] = f"{assignment['subject']} - {assignment['teacher']}"
                    else:
                        row[day] = ''
                else:
                    row[day] = ''
            writer.writerow(row)

    print(f'CSV calendar for Solution {solution["solution_number"]} generated: {csv_filename}')
