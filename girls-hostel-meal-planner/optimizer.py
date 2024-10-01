import gurobipy as gp
from gurobipy import GRB
import json


def load_data(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


def create_optimizer_model(data):
    # Extract data
    food_items = data['food_items']
    diet_types = data['diet_types']
    nutritional_info = data['nutritional_info']
    inventory_info = data['inventory_info']
    logistic_info = data['logistic_info']
    planning_info = data['planning_info']
    cost_factors = data['cost_factors']
    sustainability_metrics = data['sustainability_metrics']

    # Assume prior inventory is provided in inventory_info
    prior_inventory = inventory_info.get(
        'prior_inventory', {item: inventory_info['min_threshold'][item] for item in food_items})

    # Create a new model
    model = gp.Model("Advanced_Dietary_Supply_Chain_Optimizer")

    # Time periods
    periods = range(planning_info['horizon_days'])

    # Decision Variables
    purchase = model.addVars(food_items, periods, vtype=GRB.INTEGER, name="Purchase")
    inventory = model.addVars(food_items, periods, vtype=GRB.INTEGER, name="Inventory")
    delivery = model.addVars(periods, vtype=GRB.BINARY, name="Delivery")

    # Slack Variables for Cooking Oil Inventory Balance
    cooking_oil_slack = model.addVars(periods, vtype=GRB.CONTINUOUS, name="CookingOilSlack")

    protein_slack_vegetarian = model.addVar(vtype=GRB.CONTINUOUS, name="ProteinSlackVegetarian")

    # Objective Function
    model.setObjective(
        gp.quicksum(purchase[i, t] * food_items[i]['cost'] for i in food_items for t in periods) +
        gp.quicksum(delivery[t] * logistic_info['transport_cost'] for t in periods) +
        gp.quicksum(inventory[i, t] * cost_factors['storage_cost_per_kg_per_day'] for i in food_items for t in periods) +
        1000000 * cooking_oil_slack.sum() +
        1000000 * protein_slack_vegetarian,  # High penalty for using slack

        GRB.MINIMIZE
    )

    # Calculate total daily consumption for each food item
    total_daily_consumption = {
        item: sum(diet_types[d]['daily_consumption'].get(item, 0) * diet_types[d]['num_people']
                  for d in diet_types)
        for item in food_items
    }

    # Constraints
    # Inventory balance
    for i in food_items:
        for t in periods:
            if i == 'cooking_oil':
                if t == 0:
                    model.addConstr(
                        inventory[i, t] == prior_inventory[i] + purchase[i, t] -
                        total_daily_consumption[i] + cooking_oil_slack[t],
                        name=f"InventoryBalance_{i}_{t}"
                    )
                else:
                    model.addConstr(
                        inventory[i, t] == inventory[i, t-1] + purchase[i, t] -
                        total_daily_consumption[i] + cooking_oil_slack[t],
                        name=f"InventoryBalance_{i}_{t}"
                    )
            else:
                if t == 0:
                    model.addConstr(
                        inventory[i, t] == prior_inventory[i] + purchase[i, t] - total_daily_consumption[i],
                        name=f"InventoryBalance_{i}_{t}"
                    )
                else:
                    model.addConstr(
                        inventory[i, t] == inventory[i, t-1] + purchase[i, t] - total_daily_consumption[i],
                        name=f"InventoryBalance_{i}_{t}"
                    )

        # Ensure inventory is within allowed range
        for t in periods:
            model.addConstr(inventory[i, t] >= inventory_info['min_threshold'][i],
                            name=f"MinInventory_{i}_{t}")
            model.addConstr(inventory[i, t] <= inventory_info['max_threshold'][i],
                            name=f"MaxInventory_{i}_{t}")

    # Total inventory volume
    for t in periods:
        model.addConstr(gp.quicksum(inventory[i, t] * food_items[i]['volume_per_kg'] for i in food_items) <= inventory_info['storage_capacity'],
                        name=f"TotalInventoryVolume_{t}")

    # Nutritional requirements
    for d in diet_types:
        for t in periods:
            # Protein requirement
            model.addConstr(
                gp.quicksum(
                    food_items[i]['protein'] *
                    diet_types['vegetarian']['daily_consumption'].get(i, 0) * diet_types['vegetarian']['num_people']
                    for i in food_items
                ) + protein_slack_vegetarian >= nutritional_info['min_protein']['vegetarian'],
                name="ProteinRequirement_vegetarian_0"
            )
            # Carbohydrate limit
            model.addConstr(gp.quicksum(
                food_items[i]['carbs'] * diet_types[d]['daily_consumption'].get(i, 0) * diet_types[d]['num_people']
                for i in food_items
            ) <= nutritional_info['max_carbs'][d], name=f"CarbLimit_{d}_{t}")

    # Vehicle capacity
    for t in periods:
        model.addConstr(gp.quicksum(purchase[i, t] for i in food_items) <= logistic_info['vehicle_capacity'] * delivery[t],
                        name=f"VehicleCapacity_{t}")

    # Maximum deliveries per week
    for week in range(planning_info['horizon_days'] // 7):
        model.addConstr(gp.quicksum(delivery[t] for t in range(week*7, (week+1)*7)) <= logistic_info['max_deliveries_per_week'],
                        name=f"MaxDeliveriesPerWeek_{week}")

    # Minimum days between purchases
    min_days = logistic_info['min_days_between_purchases']
    for t in range(planning_info['horizon_days'] - min_days + 1):
        model.addConstr(gp.quicksum(delivery[t+i] for i in range(min_days)) <= 1,
                        name=f"MinDaysBetweenPurchases_{t}")

    return model


def main():
    data = load_data('data.json')
    model = create_optimizer_model(data)

    # Set Gurobi parameters
    model.Params.OutputFlag = 1  # Enable solver output
    model.Params.TimeLimit = 300  # Set a time limit of 300 seconds

    # Optimize the model
    model.optimize()

    # Check the optimization status
    if model.status == GRB.OPTIMAL:
        print("Optimal solution found")
        obj_val = model.objVal
        print(f"Total Cost: ${obj_val:.2f}")

        # Print cooking oil slack variables
        print("\nCooking Oil Slack Variables:")
        for v in model.getVars():
            if v.varName.startswith("CookingOilSlack") and v.x != 0:
                print(f"{v.varName} = {v.x}")
        
        # print(f"Protein Slack for Vegetarian Diet: {protein_slack_vegetarian.x}")

        # Print purchase schedule
        print("\nPurchase Schedule:")
        for v in model.getVars():
            if v.varName.startswith("Purchase") and v.x > 0:
                print(f"{v.varName} = {v.x}")

        # Print inventory levels
        print("\nInventory Levels:")
        for v in model.getVars():
            if v.varName.startswith("Inventory"):
                print(f"{v.varName} = {v.x}")

        # Print delivery schedule
        print("\nDelivery Schedule:")
        for v in model.getVars():
            if v.varName.startswith("Delivery") and v.x > 0:
                print(f"{v.varName} = {v.x}")

    elif model.status == GRB.INFEASIBLE:
        print("Model is infeasible")
        model.computeIIS()
        model.write("model.ilp")
        print("IIS written to file 'model.ilp'")

    elif model.status == GRB.UNBOUNDED:
        print("Model is unbounded")
    else:
        print(f"Optimization was stopped with status {model.status}")


if __name__ == "__main__":
    main()
