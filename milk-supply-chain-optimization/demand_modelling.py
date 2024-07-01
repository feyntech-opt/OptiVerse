import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Setting random seed for reproducibility
np.random.seed(42)

# Constants
days_in_year = 365
weeks_in_year = 52
months_in_year = 12
talukas_in_india = 5893  # Approximately total Talukas in India
amul_coverage = 0.05  # 5% of India Talukas
covered_talukas = int(talukas_in_india * amul_coverage)
products_daily = ['Milk']
products_weekly = ['Yogurt', 'Paneer']
products_monthly = ['Butter', 'Cheese', 'Ghee', 'Ice Cream']

# Seasonal adjustments
seasonal_adjustment_daily = np.concatenate([
    np.linspace(1.2, 1.0, 90),  # Oct to Dec (Festive/Winter - High demand)
    np.linspace(1.0, 0.8, 91),  # Jan to Mar (Winter - Moderate demand)
    np.linspace(0.8, 1.0, 92),  # Apr to Jun (Summer - Moderate demand)
    np.linspace(1.0, 1.2, 92)   # Jul to Sep (Monsoon - Moderate demand)
])

# Base demand values
base_demand = {
    'Milk': 1000,
    'Butter': 100,
    'Cheese': 80,
    'Ghee': 50,
    'Yogurt': 150,
    'Paneer': 70,
    'Ice Cream': 200
}

# Generate daily demand data
def generate_daily_demand():
    daily_demand = []
    for day in range(days_in_year):
        for taluka in range(covered_talukas):
            for product in products_daily:
                demand = base_demand[product] * seasonal_adjustment_daily[day] * np.random.uniform(0.8, 1.2)
                daily_demand.append([day, taluka, product, demand])
    return daily_demand

# Generate weekly demand data
def generate_weekly_demand():
    weekly_demand = []
    for week in range(weeks_in_year):
        for taluka in range(covered_talukas):
            for product in products_weekly:
                week_factor = np.mean(seasonal_adjustment_daily[week*7:(week+1)*7])
                demand = base_demand[product] * week_factor * 7 * np.random.uniform(0.8, 1.2)
                for day in range(week*7, (week+1)*7):
                    weekly_demand.append([day, taluka, product, demand / 7])
    return weekly_demand

# Generate monthly demand data
def generate_monthly_demand():
    monthly_demand = []
    for month in range(months_in_year):
        for taluka in range(covered_talukas):
            for product in products_monthly:
                month_factor = np.mean(seasonal_adjustment_daily[month*30:(month+1)*30])
                demand = base_demand[product] * month_factor * 30 * np.random.uniform(0.8, 1.2)
                for day in range(month*30, (month+1)*30):
                    monthly_demand.append([day, taluka, product, demand / 30])
    return monthly_demand

# Generate the data for 5% coverage
daily_demand_data = generate_daily_demand()
weekly_demand_data = generate_weekly_demand()
monthly_demand_data = generate_monthly_demand()


# Constants for scaling
total_india_demand_mpta = 330
amul_percentage = 0.2
target_amul_demand_mpta = total_india_demand_mpta * amul_percentage

# Function to generate demand data
def generate_demand_data(coverage_percentage):
    # Calculate the number of covered talukas
    covered_talukas = int(talukas_in_india * coverage_percentage)
    
    # Generate daily, weekly, and monthly demand data
    daily_demand_data = generate_daily_demand()
    weekly_demand_data = generate_weekly_demand()
    monthly_demand_data = generate_monthly_demand()
    
    # Create DataFrames for the generated data
    daily_df = pd.DataFrame(daily_demand_data, columns=['Day', 'Taluka', 'Product', 'Demand'])
    weekly_df = pd.DataFrame(weekly_demand_data, columns=['Day', 'Taluka', 'Product', 'Demand'])
    monthly_df = pd.DataFrame(monthly_demand_data, columns=['Day', 'Taluka', 'Product', 'Demand'])
    
    # Merge DataFrames
    combined_df = pd.concat([daily_df, weekly_df, monthly_df], ignore_index=True)
    
    return combined_df

# Function to scale demand based on chosen coverage percentage
def scale_demand_based_on_coverage(coverage_percentage):
    combined_df = generate_demand_data(coverage_percentage)
    
    # Aggregate demand by day and product
    agg_demand_df = combined_df.groupby(['Day', 'Product'])['Demand'].sum().reset_index()
    
    # Calculate the current total yearly demand in MTPA
    current_total_demand = combined_df['Demand'].sum() / 1000  # Convert to MTPA
    
    # Calculate the target total demand for the chosen coverage
    target_total_demand = target_amul_demand_mpta * coverage_percentage
    
    # Calculate scaling factor
    scaling_factor = target_total_demand / current_total_demand
    
    # Apply scaling factor to the demand data
    combined_df['Scaled_Demand'] = combined_df['Demand'] * scaling_factor
    
    # Calculate the scaled total yearly demand
    scaled_total_yearly_demand = combined_df['Scaled_Demand'].sum() / 1000  # Convert to MTPA
    
    # Calculate the scaled average daily demand per taluka
    scaled_average_daily_demand_per_taluka = combined_df.groupby(['Day', 'Taluka'])['Scaled_Demand'].sum().mean()
    
    return scaled_total_yearly_demand, scaled_average_daily_demand_per_taluka

# Example usage with 5% coverage
coverage_percentage = 0.05
scaled_total_yearly_demand, scaled_average_daily_demand_per_taluka = scale_demand_based_on_coverage(coverage_percentage)
scaled_total_yearly_demand, scaled_average_daily_demand_per_taluka

# Create DataFrames for 5% coverage
daily_df = pd.DataFrame(daily_demand_data, columns=['Day', 'Taluka', 'Product', 'Demand'])
weekly_df = pd.DataFrame(weekly_demand_data, columns=['Day', 'Taluka', 'Product', 'Demand'])
monthly_df = pd.DataFrame(monthly_demand_data, columns=['Day', 'Taluka', 'Product', 'Demand'])

# Merge DataFrames
combined_df = pd.concat([daily_df, weekly_df, monthly_df], ignore_index=True)

# Aggregate demand by day and product
agg_demand_df = combined_df.groupby(['Day', 'Product'])['Demand'].sum().reset_index()

# Convert Day to Date for plotting
agg_demand_df['Date'] = pd.date_range(start='2025-01-01', periods=len(agg_demand_df))

# Plotting
plt.figure(figsize=(14, 8))

for product in products_daily + products_weekly + products_monthly:
    product_data = agg_demand_df[agg_demand_df['Product'] == product]
    plt.plot(product_data['Date'], product_data['Demand'], label=product)

plt.xlabel('Date in 2025')
plt.ylabel('Total Demand')
plt.title('Daily Demand for Milk and Other Dairy Products (5% Coverage)')
plt.legend()
plt.grid(True)
plt.show()
print()
