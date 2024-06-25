import pandas as pd
import gurobipy as gp
from gurobipy import GRB
import textwrap


# Read the CSV files
human_requirements = pd.read_csv('ai-model-assignment/Human_Requirements.csv')
ai_models = pd.read_csv('ai-model-assignment/AI_Model_Details_With_Scores.csv')

# Create a detailed list of roles with separate entries for each employee
detailed_roles = []
for _, row in human_requirements.iterrows():
    for i in range(row['Number of Employees']):
        detailed_roles.append({
            'Role': f"{row['Role']} {i+1}",
            'Equivalent Tokens': int(row['Equivalent Tokens'].replace(' tokens', '').replace(',', '')),
            'AI Model Type': row['AI Model Type']
        })

# Convert the detailed roles into a DataFrame
roles_df = pd.DataFrame(detailed_roles)

# Extract necessary information
roles = roles_df['Role'].tolist()
role_tokens = roles_df['Equivalent Tokens'].tolist()
role_types = roles_df['AI Model Type'].tolist()

model_names = ai_models['Model'].tolist()
model_types = ai_models['Type'].tolist()
model_prices = ai_models['Price'].tolist()
model_scores = ai_models['MMLU Score'].astype(float).tolist()

# Create a new model
model = gp.Model("AI_Model_Assignment")

# Define decision variables
assignment_vars = {}
for i in range(len(roles)):
    for j in range(len(model_names)):
        assignment_vars[i, j] = model.addVar(vtype=GRB.BINARY, name=f"Assign_{i}_{j}")

# Objective function: Minimize token costs
obj = gp.quicksum(assignment_vars[i, j] * (model_prices[j] / 1000) * min(role_tokens[i], ai_models['Context Length'][j])
                  for i in range(len(roles)) for j in range(len(model_names)))
model.setObjective(obj, GRB.MINIMIZE)

# Constraints
# Each role should be assigned exactly one model of the appropriate type
for i in range(len(roles)):
    compatible_models = [j for j in range(len(model_names)) if role_types[i] == model_types[j]]
    if not compatible_models:
        print(f"Warning: No compatible models for role {roles[i]} of type {role_types[i]}")
    else:
        model.addConstr(gp.quicksum(assignment_vars[i, j] for j in compatible_models) == 1, f"OneModelPerRole_{i}")

# Add a constraint to ensure all roles are assigned
model.addConstr(gp.quicksum(assignment_vars[i, j] for i in range(len(roles))
                for j in range(len(model_names))) == len(roles), "AllRolesAssigned")

# Ensure the average MMLU score of the assigned models meets or exceeds a predefined threshold
threshold = 75
model.addConstr(gp.quicksum(assignment_vars[i, j] * model_scores[j]
                for i in range(len(roles)) for j in range(len(model_names))) / len(roles) >= threshold,
                "AverageMMULScore")

# Optimize the model
model.optimize()

if model.status == GRB.OPTIMAL:
    assignments = []
    total_cost = 0
    assigned_scores = []
    
    print("\n" + "="*120)
    print("{:<30} {:<15} {:<20} {:<10} {:<20} {:<15}".format(
        "Role", "Model", "Type", "Price/1K", "Tokens", "Cost"))
    print("{:<30} {:<15} {:<20} {:<10} {:<20} {:<15}".format(
        "", "", "", "", "MMLU Score", ""))
    print("-"*120)
    
    for i in range(len(roles)):
        for j in range(len(model_names)):
            if assignment_vars[i, j].X > 0.5:
                assignments.append((i, j))
                tokens_used = min(role_tokens[i], ai_models['Context Length'][j])
                cost = (model_prices[j] / 1000) * tokens_used
                total_cost += cost
                assigned_scores.append(model_scores[j])
                
                role_name = roles[i]
                model_name = textwrap.shorten(model_names[j], width=13, placeholder="...")
                
                print("{:<30} {:<15} {:<20} ${:<9.2f} {:<20,d} ${:<14.2f}".format(
                    role_name, model_name, model_types[j], model_prices[j],
                    tokens_used, cost))
                print("{:<30} {:<15} {:<20} {:<10} {:<20.2f} {:<15}".format(
                    "", "", "", "", model_scores[j], ""))
                print("-"*120)

    average_score = sum(assigned_scores) / len(assigned_scores)

    print("="*120)
    print(f"Total Token Cost: ${total_cost:.2f}")
    print(f"Average MMLU Score: {average_score:.2f}")
    print("="*120)

    assignments_df = pd.DataFrame([(roles[i], model_names[j]) for i, j in assignments], columns=['Role', 'Assigned Model'])
    assignments_df.to_csv('ai-model-assignment/Model_Assignments.csv', index=False)
else:
    print("No optimal solution found.")
    # ... (rest of the existing code for infeasible case)