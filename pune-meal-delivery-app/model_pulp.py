import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
from pulp import *
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def optimize_assignments(orders, agents, current_time):
    logging.info(f"Starting optimization for time: {current_time}")
    
    # Round current_time to the nearest minute
    current_time_rounded = current_time.replace(second=0, microsecond=0)
    
    relevant_orders = orders[orders['time'].dt.round('min') == current_time_rounded]
    relevant_orders = relevant_orders[relevant_orders['status'] == 'pending']
    
    if relevant_orders.empty or agents.empty:
        logging.warning(f"No relevant orders or agents at {current_time}")
        return []

    logging.info(f"Number of relevant orders: {len(relevant_orders)}")
    logging.info(f"Number of available agents: {len(agents)}")

    model = LpProblem("Food_Delivery_Optimization", LpMinimize)

    x = LpVariable.dicts("assignment", 
                         ((i, j) for i in relevant_orders.index for j in agents.index),
                         cat='Binary')

    distances = {(i, j): haversine_distance(relevant_orders.loc[i, 'restaurant_latitude'],
                                            relevant_orders.loc[i, 'restaurant_longitude'],
                                            agents.loc[j, 'current_latitude'],
                                            agents.loc[j, 'current_longitude'])
                 for i in relevant_orders.index for j in agents.index}

    # Objective: Minimize total distance
    model += lpSum(distances[(i, j)] * x[(i, j)] for i in relevant_orders.index for j in agents.index)

    # Constraints
    # Each order must be assigned to exactly one agent
    for i in relevant_orders.index:
        model += lpSum(x[(i, j)] for j in agents.index) == 1

    # Each agent can be assigned to at most one order
    for j in agents.index:
        model += lpSum(x[(i, j)] for i in relevant_orders.index) <= 1

    # Force at least one assignment if there are orders and agents
    if not relevant_orders.empty and not agents.empty:
        model += lpSum(x[(i, j)] for i in relevant_orders.index for j in agents.index) >= 1

    logging.info("Starting CBC solver")
    solver = PULP_CBC_CMD(msg=1, timeLimit=60)
    model.solve(solver)

    logging.info(f"Optimization status: {LpStatus[model.status]}")

    if model.status == LpStatusOptimal:
        assignments = []
        for i in relevant_orders.index:
            for j in agents.index:
                if x[(i, j)].value() > 0.5:
                    assignments.append({
                        'order_id': relevant_orders.loc[i, 'order_id'],
                        'agent_id': agents.loc[j, 'agent_id'],
                        'estimated_delivery_time': relevant_orders.loc[i, 'estimated_delivery_time'],
                        'customer_rating': relevant_orders.loc[i, 'customer_rating'],
                        'distance': distances[(i, j)],
                        'agent_earning': relevant_orders.loc[i, 'agent_earning'],
                        'order_zone': relevant_orders.loc[i, 'zone'],
                        'agent_zone': agents.loc[j, 'zone']
                    })
        logging.info(f"Found {len(assignments)} assignments")
        return assignments
    else:
        logging.error("Optimization failed to find an optimal solution")
        return []
    
def update_agent_status(agents, assignments, current_time, orders):
    for assignment in assignments:
        agent_id = assignment['agent_id']
        order_id = assignment['order_id']
        agent_index = agents.index[agents['agent_id'] == agent_id].item()
        order_index = orders.index[orders['order_id'] == order_id].item()
        
        agents.loc[agent_index, 'current_latitude'] = orders.loc[order_index, 'customer_latitude']
        agents.loc[agent_index, 'current_longitude'] = orders.loc[order_index, 'customer_longitude']
        agents.loc[agent_index, 'next_available_time'] = current_time + timedelta(minutes=assignment['estimated_delivery_time'])
        agents.loc[agent_index, 'daily_orders'] += 1
        agents.loc[agent_index, 'daily_earnings'] += assignment['agent_earning']
        orders.loc[order_index, 'status'] = 'assigned'

    return agents, orders

if __name__ == "__main__":
    logging.info("Starting the food delivery optimization process")

    orders = pd.read_csv("pune_orders_5min.csv")
    agents = pd.read_csv("pune_delivery_agents.csv")
    
    orders['time'] = pd.to_datetime(orders['time'])
    agents['next_available_time'] = pd.to_datetime(agents['next_available_time'])

    start_time = orders['time'].min().floor('min')
    logging.info(f"Optimizing for time: {start_time}")

    assignments = optimize_assignments(orders, agents, start_time)

    if assignments:
        agents, orders = update_agent_status(agents, assignments, start_time, orders)
        assignments_df = pd.DataFrame(assignments)

        logging.info(f"Total orders assigned: {len(assignments_df)}")
        logging.info(f"Average delivery time: {assignments_df['estimated_delivery_time'].mean():.2f} minutes")
        logging.info(f"Average distance: {assignments_df['distance'].mean():.2f} km")
        logging.info(f"Average agent earning: ₹{assignments_df['agent_earning'].mean():.2f}")

        # Debug: Check for cross-zone assignments
        cross_zone = assignments_df[assignments_df['order_zone'] != assignments_df['agent_zone']]
        logging.info(f"Cross-zone assignments: {len(cross_zone)}")

        assignments_df.to_csv("optimized_assignments_pulp_cbc_1min.csv", index=False)
        agents.to_csv("updated_agents_pulp_cbc_1min.csv", index=False)
        logging.info("Assignments saved to 'optimized_assignments_pulp_cbc_1min.csv'")
        logging.info("Updated agent data saved to 'updated_agents_pulp_cbc_1min.csv'")
    else:
        logging.warning("No assignments made.")

    logging.info(f"Total orders: {len(orders)}")
    logging.info(f"Orders in the first minute: {len(orders[orders['time'].dt.floor('min') == start_time])}")
    logging.info(f"Pending orders: {len(orders[orders['status'] == 'pending'])}")

    logging.info("Food delivery optimization process completed")