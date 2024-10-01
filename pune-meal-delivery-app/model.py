import pandas as pd
import numpy as np
from gurobipy import Model, GRB, quicksum
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def optimize_assignments(orders, agents, current_time):
    # Filter orders for the current minute only
    relevant_orders = orders[orders['time'].dt.floor('T') == current_time.floor('T')]
    relevant_orders = relevant_orders[relevant_orders['status'] == 'pending']
    
    if relevant_orders.empty or agents.empty:
        print(f"No relevant orders or agents at {current_time}")
        return []

    print(f"Number of relevant orders: {len(relevant_orders)}")
    print(f"Number of available agents: {len(agents)}")

    m = Model("Food Delivery Optimization")

    # Create variables
    x = m.addVars(relevant_orders.index, agents.index, vtype=GRB.BINARY, name="assignment")

    # Calculate distances between agents and orders
    distances = {(i, j): haversine_distance(relevant_orders.loc[i, 'restaurant_latitude'], 
                                            relevant_orders.loc[i, 'restaurant_longitude'],
                                            agents.loc[j, 'current_latitude'], 
                                            agents.loc[j, 'current_longitude'])
                 for i in relevant_orders.index for j in agents.index}

    # Set objective
    m.setObjective(
        quicksum(relevant_orders.loc[i, 'estimated_delivery_time'] * x[i, j] for i in relevant_orders.index for j in agents.index) * 0.3 +
        quicksum((1 / relevant_orders.loc[i, 'customer_rating']) * x[i, j] for i in relevant_orders.index for j in agents.index) * 0.2 +
        quicksum(distances[i, j] * x[i, j] for i in relevant_orders.index for j in agents.index) * 0.3 +
        quicksum((1 / relevant_orders.loc[i, 'agent_earning']) * x[i, j] for i in relevant_orders.index for j in agents.index) * 0.2,
        GRB.MINIMIZE
    )

    # Constraints
    # Each order is assigned to at most one agent
    m.addConstrs((quicksum(x[i, j] for j in agents.index) <= 1 for i in relevant_orders.index), "order_assignment")

    # Each agent is assigned to at most one order
    m.addConstrs((quicksum(x[i, j] for i in relevant_orders.index) <= 1 for j in agents.index), "agent_assignment")

    # Ensure agents are only assigned to orders in their zone
    m.addConstrs((x[i, j] == 0 for i in relevant_orders.index for j in agents.index 
                  if relevant_orders.loc[i, 'zone'] != agents.loc[j, 'zone']), "zone_constraint")

    # Optimize the model
    m.optimize()

    # Extract and return results
    if m.status == GRB.OPTIMAL:
        assignments = []
        for i in relevant_orders.index:
            for j in agents.index:
                if x[i, j].x > 0.5:
                    assignments.append({
                        'order_id': relevant_orders.loc[i, 'order_id'],
                        'agent_id': agents.loc[j, 'agent_id'],
                        'estimated_delivery_time': relevant_orders.loc[i, 'estimated_delivery_time'],
                        'customer_rating': relevant_orders.loc[i, 'customer_rating'],
                        'distance': distances[i, j],
                        'agent_earning': relevant_orders.loc[i, 'agent_earning']
                    })
        return assignments
    else:
        print(f"Optimization failed with status: {m.status}")
        return []

def update_agent_status(agents, assignments, current_time, orders):
    for assignment in assignments:
        agent_id = assignment['agent_id']
        order_id = assignment['order_id']
        agent_index = agents.index[agents['agent_id'] == agent_id].item()
        order_index = orders.index[orders['order_id'] == order_id].item()
        
        # Update agent location to the delivery location
        agents.loc[agent_index, 'current_latitude'] = orders.loc[order_index, 'customer_latitude']
        agents.loc[agent_index, 'current_longitude'] = orders.loc[order_index, 'customer_longitude']
        
        # Update agent availability time
        agents.loc[agent_index, 'next_available_time'] = current_time + timedelta(minutes=assignment['estimated_delivery_time'])
        
        # Update daily orders and earnings
        agents.loc[agent_index, 'daily_orders'] += 1
        agents.loc[agent_index, 'daily_earnings'] += assignment['agent_earning']

        # Update order status
        orders.loc[order_index, 'status'] = 'assigned'

    return agents, orders

# Main execution
if __name__ == "__main__":
    # Load data
    orders = pd.read_csv("pune_orders_5min.csv")
    agents = pd.read_csv("pune_delivery_agents.csv")
    
    # Convert string timestamps to datetime
    orders['time'] = pd.to_datetime(orders['time'])
    agents['next_available_time'] = pd.to_datetime(agents['next_available_time'])

    # Set simulation start time (first minute of orders)
    start_time = orders['time'].min().floor('T')

    print(f"Optimizing for time: {start_time}")

    # Optimize assignments for the first minute only
    assignments = optimize_assignments(orders, agents, start_time)

    if assignments:
        agents, orders = update_agent_status(agents, assignments, start_time, orders)
        assignments_df = pd.DataFrame(assignments)

        # Print statistics
        print(f"\nTotal orders assigned: {len(assignments_df)}")
        print(f"Average delivery time: {assignments_df['estimated_delivery_time'].mean():.2f} minutes")
        print(f"Average distance: {assignments_df['distance'].mean():.2f} km")
        print(f"Average agent earning: ₹{assignments_df['agent_earning'].mean():.2f}")

        # Save assignments and updated agent data
        assignments_df.to_csv("optimized_assignments_1min.csv", index=False)
        agents.to_csv("updated_agents_1min.csv", index=False)
        print("\nAssignments saved to 'optimized_assignments_1min.csv'")
        print("Updated agent data saved to 'updated_agents_1min.csv'")
    else:
        print("No assignments made.")

    # Print order statistics
    print("\nOrder Statistics:")
    print(f"Total orders: {len(orders)}")
    print(f"Orders in the first minute: {len(orders[orders['time'].dt.floor('T') == start_time])}")
    print(f"Pending orders: {len(orders[orders['status'] == 'pending'])}")