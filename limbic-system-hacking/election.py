from pyomo.environ import *
import numpy as np

# Number of wards
n_wards = 10

# Budget
B = 100000

# Minimum and maximum investments per ward
L = np.random.randint(5000, 10000, size=n_wards)
U = np.random.randint(10000, 20000, size=n_wards)

# Define multivariate factors for each ward (example data)
# Factors: caste, religion, age, social_issues, target_group_fit (all on a scale from 0 to 1)
factors = {
    "caste": np.random.rand(n_wards),
    "religion": np.random.rand(n_wards),
    "age": np.random.rand(n_wards),
    "social_issues": np.random.rand(n_wards),
    "target_group_fit": np.random.rand(n_wards),
}


# Expected votes function (example: linear function of investment and factors)
def expected_votes(x, f):
    return (
        100
        + 0.1 * x
        + 50 * f["caste"]
        + 30 * f["religion"]
        + 20 * f["age"]
        + 40 * f["social_issues"]
        + 60 * f["target_group_fit"]
    )


# Probability of support function (example: depends on ward characteristics)
def probability_support(f):
    return (
        0.5
        + 0.2 * f["caste"]
        + 0.1 * f["religion"]
        + 0.1 * f["age"]
        + 0.2 * f["social_issues"]
        + 0.3 * f["target_group_fit"]
    )


# Create a model
model = ConcreteModel()

# Decision variables
model.x = Var(range(n_wards), bounds=(0, None))

# Objective function
model.obj = Objective(
    expr=sum(
        expected_votes(model.x[i], {k: factors[k][i] for k in factors})
        * probability_support({k: factors[k][i] for k in factors})
        for i in range(n_wards)
    ),
    sense=maximize,
)

# Constraints
model.budget = Constraint(expr=sum(model.x[i] for i in range(n_wards)) <= B)
model.investment_limits = ConstraintList()
for i in range(n_wards):
    model.investment_limits.add(expr=model.x[i] >= L[i])
    model.investment_limits.add(expr=model.x[i] <= U[i])

# Solve the model
solver = SolverFactory("glpk")
result = solver.solve(model)

# Display results
investment_plan = [model.x[i].value for i in range(n_wards)]
print("Optimal investment plan:", investment_plan)
print(
    "Expected votes:",
    sum(
        expected_votes(investment_plan[i], {k: factors[k][i] for k in factors})
        * probability_support({k: factors[k][i] for k in factors})
        for i in range(n_wards)
    ),
)
