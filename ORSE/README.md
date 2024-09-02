Here is how you can approach writing a constraint programming model in OR-Tools for each permutation:

### Problem Description:
Given the equation:
\[ 280a + 80b + 75c + 50d + 25e - 30f - 42g = R \]
where \( a, b, c, d, e, f, g \) are strictly positive integer modifiers, and \( R \) is the solution range, your goal is to find the smallest sum of modifiers for each possible subset such that the equation result is within the given range.

### Steps to Implement:
1. **Define the problem and variables**:
   - You have seven variables \( a, b, c, d, e, f, g \).
   - Each subset will include only some of these variables (i.e., some will be set to zero).

2. **Formulate the constraints**:
   - The equation must be within the range \( R \), which you've set as -2 to -2 in the example.
   - The subset of variables you consider will be non-zero; all others should be set to zero.

3. **Objective**:
   - Minimize the sum of the non-zero variables for each subset.

4. **Modeling in OR-Tools**:
   - For each subset of \( a, b, c, d, e, f, g \), create a constraint programming model.
   - Define the equation and objective for each subset.
   - Use OR-Tools to solve the problem and retrieve the minimal solution.

Here is an example code snippet using OR-Tools in Python:

```python
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
```

### Explanation:
1. **Subset Generation**: This script generates all possible subsets of the variables.
2. **Constraint Setup**: For each subset, it sets up a constraint model using OR-Tools.
3. **Solver Execution**: It runs the solver and checks if a feasible or optimal solution is found.
4. **Results**: The minimal sum of modifiers is printed for each subset where a solution exists.

### Execution:
- Run this script in a Python environment with OR-Tools installed.
- It will generate the minimal solutions for all possible subsets of variables based on the given equation and range.

This approach ensures that you consider all subsets and find the optimal solution for each, as per your requirement.