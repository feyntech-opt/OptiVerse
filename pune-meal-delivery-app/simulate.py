import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2

# Constants
ZONES = {
    "Central Pune": {"lat_range": (18.50, 18.55), "lon_range": (73.85, 73.90)},
    "East Pune": {"lat_range": (18.52, 18.58), "lon_range": (73.95, 74.00)},
    "West Pune": {"lat_range": (18.49, 18.55), "lon_range": (73.75, 73.80)},
    "North Pune": {"lat_range": (18.60, 18.65), "lon_range": (73.78, 73.85)},
    "South Pune": {"lat_range": (18.45, 18.50), "lon_range": (73.85, 73.90)}
}

CHEFS = ["Sanjeev Kapoor", "Vikas Khanna", "Ranveer Brar", "Kunal Kapur", "Shipra Khanna"]
CUISINES = ["North Indian", "South Indian", "Chinese", "Italian", "Continental", "Fast Food"]
RESTAURANT_TYPES = ['Delight', 'Cuisine', 'Kitchen', 'Eatery', 'Bistro', 'Cafe', 'Restaurant']

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance

def generate_restaurants(num_restaurants=1000):
    zones = list(ZONES.keys())
    zone_indices = np.random.randint(0, len(zones), num_restaurants)
    
    lats = np.zeros(num_restaurants)
    lons = np.zeros(num_restaurants)
    for i, zone in enumerate(zones):
        mask = zone_indices == i
        lat_range, lon_range = ZONES[zone]["lat_range"], ZONES[zone]["lon_range"]
        lats[mask] = np.random.uniform(lat_range[0], lat_range[1], mask.sum())
        lons[mask] = np.random.uniform(lon_range[0], lon_range[1], mask.sum())
    
    chefs = np.random.choice(CHEFS, num_restaurants)
    cuisines = np.random.choice(CUISINES, num_restaurants)
    types = np.random.choice(RESTAURANT_TYPES, num_restaurants)
    
    names = [f"{chef}'s {cuisine} {type}" for chef, cuisine, type in zip(chefs, cuisines, types)]
    
    return pd.DataFrame({
        'zone': [zones[i] for i in zone_indices],
        'name': names,
        'latitude': lats,
        'longitude': lons
    })

def generate_agents(num_agents=1000, start_time=datetime(2023, 7, 16, 8, 0, 0)):
    zones = list(ZONES.keys())
    zone_indices = np.random.randint(0, len(zones), num_agents)
    
    lats = np.zeros(num_agents)
    lons = np.zeros(num_agents)
    for i, zone in enumerate(zones):
        mask = zone_indices == i
        lat_range, lon_range = ZONES[zone]["lat_range"], ZONES[zone]["lon_range"]
        lats[mask] = np.random.uniform(lat_range[0], lat_range[1], mask.sum())
        lons[mask] = np.random.uniform(lon_range[0], lon_range[1], mask.sum())
    
    return pd.DataFrame({
        'agent_id': np.arange(1, num_agents + 1),
        'zone': [zones[i] for i in zone_indices],
        'rating': np.round(np.random.uniform(3.0, 5.0, num_agents), 1),
        'daily_orders': np.zeros(num_agents, dtype=int),
        'daily_earnings': np.zeros(num_agents),
        'seniority': np.random.choice(['Junior', 'Mid', 'Senior'], num_agents),
        'home_latitude': lats,
        'home_longitude': lons,
        'current_latitude': lats,
        'current_longitude': lons,
        'status': 'available',
        'next_available_time': [start_time] * num_agents
    })

def generate_orders(restaurants, start_time, duration_minutes=1, orders_per_minute=20):
    num_orders = duration_minutes * orders_per_minute
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    order_times = [start_time + timedelta(seconds=np.random.randint(0, duration_minutes * 60)) for _ in range(num_orders)]
    order_times.sort()
    
    restaurant_sample = restaurants.sample(n=num_orders, replace=True)
    
    customer_lats = np.zeros(num_orders)
    customer_lons = np.zeros(num_orders)
    for zone in ZONES:
        mask = restaurant_sample['zone'] == zone
        lat_range, lon_range = ZONES[zone]["lat_range"], ZONES[zone]["lon_range"]
        customer_lats[mask] = np.random.uniform(lat_range[0], lat_range[1], mask.sum())
        customer_lons[mask] = np.random.uniform(lon_range[0], lon_range[1], mask.sum())
    
    # Generate order details
    food_costs = np.round(np.random.uniform(300, 400, num_orders), 2)
    delivery_charges = np.round(np.random.uniform(20, 50, num_orders), 2)
    packaging_charges = np.round(np.random.uniform(10, 30, num_orders), 2)
    service_fees = np.round(food_costs * np.random.uniform(0.05, 0.10, num_orders), 2)
    gst = np.round((food_costs + delivery_charges + packaging_charges + service_fees) * 0.05, 2)
    total_costs = np.round(food_costs + delivery_charges + packaging_charges + service_fees + gst, 2)
    
    customer_ratings = np.round(np.random.uniform(1.0, 5.0, num_orders), 1)
    tips = np.round(np.random.exponential(scale=20, size=num_orders), 2)  # Tips in rupees
    
    preparation_times = np.random.randint(10, 31, num_orders)  # Preparation time in minutes
    
    # Calculate actual distances using Haversine formula
    distances = [haversine_distance(restaurant_sample.iloc[i]['latitude'], restaurant_sample.iloc[i]['longitude'],
                                    customer_lats[i], customer_lons[i]) for i in range(num_orders)]
    distances = np.round(distances, 2)
    
    # Estimate delivery times based on actual distances
    speed = 20  # Average speed in km/h
    delivery_times = np.round(np.array(distances) / speed * 60 + preparation_times, 2)  # Delivery time in minutes
    
    # Calculate delivery agent fees
    base_fees = np.round(np.random.uniform(20, 40, num_orders), 2)
    incentives = np.round(np.random.uniform(10, 50, num_orders), 2)
    agent_earnings = np.round(base_fees + incentives, 2)
    
    return pd.DataFrame({
        'order_id': np.arange(1, num_orders + 1),
        'time': order_times,
        'zone': restaurant_sample['zone'].values,
        'restaurant': restaurant_sample['name'].values,
        'restaurant_latitude': restaurant_sample['latitude'].values,
        'restaurant_longitude': restaurant_sample['longitude'].values,
        'customer_latitude': customer_lats,
        'customer_longitude': customer_lons,
        'food_cost': food_costs,
        'delivery_charges': delivery_charges,
        'packaging_charges': packaging_charges,
        'service_fees': service_fees,
        'gst': gst,
        'total_cost': total_costs,
        'customer_rating': customer_ratings,
        'tip': tips,
        'preparation_time': preparation_times,
        'distance': distances,
        'estimated_delivery_time': delivery_times,
        'base_fee': base_fees,
        'incentive': incentives,
        'agent_earning': agent_earnings,
        'status': 'pending'
    })

if __name__ == "__main__":
    import time
    start = time.time()

    print("Generating restaurant data...")
    restaurants = generate_restaurants()
    restaurants.to_csv("pune_restaurants.csv", index=False)
    print(f"Generated {len(restaurants)} restaurants")
    print(f"Unique restaurant names: {restaurants['name'].nunique()}")

    print("\nGenerating agent data...")
    agents = generate_agents()
    agents.to_csv("pune_delivery_agents.csv", index=False)
    print(f"Generated {len(agents)} delivery agents")

    print("\nGenerating order data for 5 minutes...")
    start_time = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)  # Start at noon
    orders = generate_orders(restaurants, start_time)
    orders.to_csv("pune_orders_5min.csv", index=False)
    print(f"Generated {len(orders)} orders")

    end = time.time()
    print(f"\nData generation completed in {end - start:.2f} seconds")

    print("\nResults saved to 'pune_restaurants.csv', 'pune_delivery_agents.csv', and 'pune_orders_5min.csv'")

    # Display some statistics about the generated data
    print("\nOrder Statistics:")
    print(f"Average food cost: ₹{orders['food_cost'].mean():.2f}")
    print(f"Average delivery charges: ₹{orders['delivery_charges'].mean():.2f}")
    print(f"Average packaging charges: ₹{orders['packaging_charges'].mean():.2f}")
    print(f"Average service fees: ₹{orders['service_fees'].mean():.2f}")
    print(f"Average GST: ₹{orders['gst'].mean():.2f}")
    print(f"Average total cost: ₹{orders['total_cost'].mean():.2f}")
    print(f"Average customer rating: {orders['customer_rating'].mean():.2f}")
    print(f"Average tip: ₹{orders['tip'].mean():.2f}")
    print(f"Average preparation time: {orders['preparation_time'].mean():.2f} minutes")
    print(f"Average estimated delivery time: {orders['estimated_delivery_time'].mean():.2f} minutes")
    print(f"Average delivery distance: {orders['distance'].mean():.2f} km")
    print(f"Average agent earning per order: ₹{orders['agent_earning'].mean():.2f}")