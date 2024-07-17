import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from simulate import generate_restaurants, generate_agents, generate_orders
from model_pulp import optimize_assignments, update_agent_status
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_kpis(assignments, all_orders, agents, minute):
    total_orders = len(all_orders[all_orders['time'].dt.floor('min') == minute])
    assigned_orders = len(assignments)
    
    kpis = {
        'minute': minute,
        'order_fulfillment_rate': assigned_orders / total_orders if total_orders > 0 else 0,
        'average_delivery_time': np.mean([a['estimated_delivery_time'] for a in assignments]) if assignments else 0,
        'average_distance': np.mean([a['distance'] for a in assignments]) if assignments else 0,
        'agent_utilization': len(agents[agents['status'] == 'busy']) / len(agents),
        'revenue': sum([a['agent_earning'] for a in assignments])
    }
    return kpis

def run_hourly_optimization(restaurants, agents, start_time):
    all_assignments = []
    all_orders = pd.DataFrame()
    current_time = start_time
    kpis_list = []

    for minute in range(60):
        logging.info(f"Optimizing for minute {minute + 1}, time: {current_time}")

        new_orders = generate_orders(restaurants, current_time, duration_minutes=1, orders_per_minute=20)
        all_orders = pd.concat([all_orders, new_orders], ignore_index=True)

        assignments = optimize_assignments(all_orders, agents, current_time)

        if assignments:
            all_assignments.extend(assignments)
            try:
                agents, all_orders = update_agent_status(agents, assignments, current_time, all_orders)
                logging.info(f"Minute {minute + 1}: Assigned {len(assignments)} orders")
            except Exception as e:
                logging.error(f"Error updating agent status: {str(e)}")
                logging.info("Continuing to next minute...")
        else:
            logging.info(f"Minute {minute + 1}: No assignments made")

        # Calculate and store KPIs
        kpis = calculate_kpis(assignments, all_orders, agents, current_time)
        kpis_list.append(kpis)

        current_time += timedelta(minutes=1)

    return all_assignments, agents, all_orders, pd.DataFrame(kpis_list)

def create_dashboard(kpis_df):
    plt.figure(figsize=(20, 15))
    plt.suptitle("Food Delivery KPI Dashboard", fontsize=20)

    # Order Fulfillment Rate
    plt.subplot(3, 2, 1)
    sns.lineplot(x='minute', y='order_fulfillment_rate', data=kpis_df)
    plt.title('Order Fulfillment Rate')
    plt.ylabel('Rate')

    # Average Delivery Time
    plt.subplot(3, 2, 2)
    sns.lineplot(x='minute', y='average_delivery_time', data=kpis_df)
    plt.title('Average Delivery Time')
    plt.ylabel('Minutes')

    # Average Distance
    plt.subplot(3, 2, 3)
    sns.lineplot(x='minute', y='average_distance', data=kpis_df)
    plt.title('Average Delivery Distance')
    plt.ylabel('Kilometers')

    # Agent Utilization
    plt.subplot(3, 2, 4)
    sns.lineplot(x='minute', y='agent_utilization', data=kpis_df)
    plt.title('Agent Utilization')
    plt.ylabel('Rate')

    # Revenue
    plt.subplot(3, 2, 5)
    sns.lineplot(x='minute', y='revenue', data=kpis_df)
    plt.title('Revenue per Minute')
    plt.ylabel('Rupees')

    # Cumulative Revenue
    plt.subplot(3, 2, 6)
    sns.lineplot(x='minute', y=kpis_df['revenue'].cumsum(), data=kpis_df)
    plt.title('Cumulative Revenue')
    plt.ylabel('Rupees')

    plt.tight_layout()
    plt.savefig('food_delivery_dashboard.png')
    plt.close()

if __name__ == "__main__":
    logging.info("Starting the hourly food delivery optimization process")

    restaurants = generate_restaurants()
    start_time = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    agents = generate_agents(start_time=start_time)

    logging.info(f"Starting optimization from: {start_time}")

    all_assignments, updated_agents, updated_orders, kpis_df = run_hourly_optimization(restaurants, agents, start_time)

    assignments_df = pd.DataFrame(all_assignments)

    if not assignments_df.empty:
        logging.info(f"Total orders assigned: {len(assignments_df)}")
        logging.info(f"Average delivery time: {assignments_df['estimated_delivery_time'].mean():.2f} minutes")
        logging.info(f"Average distance: {assignments_df['distance'].mean():.2f} km")
        logging.info(f"Average agent earning: ₹{assignments_df['agent_earning'].mean():.2f}")

        cross_zone = assignments_df[assignments_df['order_zone'] != assignments_df['agent_zone']]
        logging.info(f"Cross-zone assignments: {len(cross_zone)}")

        assignments_df.to_csv("hourly_optimized_assignments.csv", index=False)
        updated_agents.to_csv("hourly_updated_agents.csv", index=False)
        updated_orders.to_csv("hourly_updated_orders.csv", index=False)
        kpis_df.to_csv("hourly_kpis.csv", index=False)
        
        logging.info("Results and KPIs saved to CSV files")

        # Create and save the dashboard
        create_dashboard(kpis_df)
        logging.info("Dashboard created and saved as 'food_delivery_dashboard.png'")
    else:
        logging.warning("No assignments made during the entire hour.")

    logging.info(f"Total orders: {len(updated_orders)}")
    logging.info(f"Orders assigned: {len(updated_orders[updated_orders['status'] == 'assigned'])}")
    logging.info(f"Orders still pending: {len(updated_orders[updated_orders['status'] == 'pending'])}")

    logging.info("Hourly food delivery optimization process completed")