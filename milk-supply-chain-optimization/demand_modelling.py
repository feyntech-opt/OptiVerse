import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Read the CSV file
retail_units_df = pd.read_csv('data/supply_chain_units.csv')

# Filter retail units (assuming there's a column that identifies retail units)
retail_units = retail_units_df[retail_units_df['UnitType'] == 'Retail']  # Adjust 'Type' to the actual column name

# Get the number of retail units
NUM_RETAIL_UNITS = len(retail_units)

print(f"Number of retail units: {NUM_RETAIL_UNITS}")

# Constants
TOTAL_ANNUAL_DEMAND = 20_000_000  # 20 MTPA in kg
DAYS_IN_YEAR = 365

# Product information from the JSON data
products = {
    "Milk": {"shelf_life": 10, "time_unit": "daily", "relative_demand": 0.50},
    "Butter": {"shelf_life": 90, "time_unit": "weekly", "relative_demand": 0.10},
    "Cheese": {"shelf_life": 120, "time_unit": "weekly", "relative_demand": 0.05},
    "Ghee": {"shelf_life": 365, "time_unit": "monthly", "relative_demand": 0.10},
    "Yogurt": {"shelf_life": 21, "time_unit": "daily", "relative_demand": 0.15},
    "Paneer": {"shelf_life": 14, "time_unit": "daily", "relative_demand": 0.05},
    "Ice Cream": {"shelf_life": 120, "time_unit": "weekly", "relative_demand": 0.05}
}

def seasonal_factor(day_of_year, product):
    base = 1 + 0.2 * np.sin(2 * np.pi * day_of_year / 365)
    if product in ["Milk", "Yogurt", "Ice Cream"]:
        # Higher demand in summer
        return base + 0.1 * np.sin(np.pi * day_of_year / 365)
    elif product in ["Butter", "Ghee"]:
        # Higher demand in winter
        return base - 0.1 * np.sin(np.pi * day_of_year / 365)
    else:
        return base

def festive_factor(date):
    # Example festive seasons (adjust as needed)
    festive_dates = [
        (datetime(2025, 1, 14), datetime(2025, 1, 15)),  # Makar Sankranti
        (datetime(2025, 3, 17), datetime(2025, 3, 18)),  # Holi
        (datetime(2025, 8, 19), datetime(2025, 8, 19)),  # Janmashtami
        (datetime(2025, 10, 12), datetime(2025, 10, 21)),  # Navratri
        (datetime(2025, 11, 12), datetime(2025, 11, 16)),  # Diwali
        (datetime(2025, 12, 25), datetime(2025, 12, 25))   # Christmas
    ]
    
    for start, end in festive_dates:
        if start <= date <= end:
            return 1.2  # 20% increase during festive seasons
    return 1.0

def generate_demand_data(start_date, end_date):
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    demand_data = []

    for product, info in products.items():
        annual_demand = TOTAL_ANNUAL_DEMAND * info['relative_demand']
        
        if info['time_unit'] == 'daily':
            daily_demand = annual_demand / DAYS_IN_YEAR
            for date in date_range:
                day_of_year = date.dayofyear
                seasonal_demand = daily_demand * seasonal_factor(day_of_year, product) * festive_factor(date)
                for _, retail_unit in retail_units.iterrows():
                    demand = np.random.normal(seasonal_demand / NUM_RETAIL_UNITS, seasonal_demand / NUM_RETAIL_UNITS / 10)
                    demand_data.append({
                        'Date': date,
                        'Product': product,
                        'Retail_Unit_ID': retail_unit['UnitID'],  # Adjust 'ID' to the actual column name
                        'Demand': max(0, demand)
                    })
        
        elif info['time_unit'] == 'weekly':
            weekly_demand = annual_demand / 52
            for date in date_range[::7]:
                day_of_year = date.dayofyear
                seasonal_demand = weekly_demand * seasonal_factor(day_of_year, product) * festive_factor(date)
                for _, retail_unit in retail_units.iterrows():
                    demand = np.random.normal(seasonal_demand / NUM_RETAIL_UNITS, seasonal_demand / NUM_RETAIL_UNITS / 10)
                    demand_data.append({
                        'Date': date,
                        'Product': product,
                        'Retail_Unit_ID': retail_unit['UnitID'],  # Adjust 'ID' to the actual column name
                        'Demand': max(0, demand)
                    })
        
        elif info['time_unit'] == 'monthly':
            monthly_demand = annual_demand / 12
            for date in date_range[date_range.day == 1]:
                day_of_year = date.dayofyear
                seasonal_demand = monthly_demand * seasonal_factor(day_of_year, product) * festive_factor(date)
                for _, retail_unit in retail_units.iterrows():
                    demand = np.random.normal(seasonal_demand / NUM_RETAIL_UNITS, seasonal_demand / NUM_RETAIL_UNITS / 10)
                    demand_data.append({
                        'Date': date,
                        'Product': product,
                        'Retail_Unit_ID': retail_unit['UnitID'],  # Adjust 'ID' to the actual column name
                        'Demand': max(0, demand)
                    })

    return pd.DataFrame(demand_data)

# Generate demand data for the year 2025
demand_df = generate_demand_data('2025-01-01', '2025-12-31')

# Verify total annual demand
total_demand = demand_df['Demand'].sum()
print(f"Total annual demand: {total_demand:.2f} kg")
print(f"Difference from target: {(total_demand - TOTAL_ANNUAL_DEMAND) / TOTAL_ANNUAL_DEMAND * 100:.2f}%")

# Display sample of the data
print(demand_df.head(10))

# Save the data to a CSV file
demand_df.to_csv('data/amul_retail_demand_2025_revised.csv', index=False)