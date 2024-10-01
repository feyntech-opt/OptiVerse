from ortools.sat.python import cp_model

def solve_for_subset(subset, R_min, R_max):
    # Create the model
    model = cp_model.CpModel()

    # Create the variables
    a = model.NewIntVar(0, 1000, 'a') if 'a' in subset else 0
    b = model.NewIntVar(0, 1000, 'b') if 'b' in subset else 0
    c = model.NewIntVar(0, 1000, 'c') if 'c' in subset else 0
    d = model.NewIntVar(0, 1000, 'd') if 'd' in subset else 0
    e = model.NewIntVar(0, 1000, 'e') if 'e' in subset else 0
    f = model.NewIntVar(0, 1000, 'f') if 'f' in subset else 0
    g = model.NewIntVar(0, 1000, 'g') if 'g' in subset else 0

    # Define the equation constraint
    equation = 280 * a + 80 * b + 75 * c + 50 * d + 25 * e - 30 * f - 42 * g
    model.Add(equation >= R_min)
    model.Add(equation <= R_max)

    # Define the objective (minimize the sum of non-zero variables)
    model.Minimize(a + b + c + d + e + f + g)

    # Create a solver and solve
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # Check the status and print the solution
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        return {
            'a': solver.Value(a),
            'b': solver.Value(b),
            'c': solver.Value(c),
            'd': solver.Value(d),
            'e': solver.Value(e),
            'f': solver.Value(f),
            'g': solver.Value(g),
            'value': solver.ObjectiveValue()
        }
    else:
        return None

def generate_all_subsets():
    variables = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
    subsets = []
    for i in range(1, 2 ** len(variables)):
        subset = [variables[j] for j in range(len(variables)) if (i & (1 << j)) > 0]
        subsets.append(subset)
    return subsets

# Define the range
R_min = -2
R_max = -2

# Solve for all subsets
all_subsets = generate_all_subsets()
solutions = []

for subset in all_subsets:
    solution = solve_for_subset(subset, R_min, R_max)
    if solution:
        solutions.append((subset, solution))

# Print the solutions
for subset, solution in solutions:
    print(f'Subset: {subset}')
    print(f'Solution: {solution}')
    print()
