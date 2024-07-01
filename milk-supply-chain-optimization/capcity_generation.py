import pandas as pd
import numpy as np
import random

# Setting random seed for reproducibility
np.random.seed(42)

# Load the existing processed Amul location data
df_amul = pd.read_csv('milk-supply-chain-optimization/updated_India_pincode_list.csv')

# Filter for plants only
plants_df = df_amul[df_amul['CenterType'] == 'Plant'].copy()

# List of products
products = ['Milk', 'Butter', 'Cheese', 'Ghee', 'Yogurt', 'Paneer', 'Ice Cream']

# Function to generate random capacity for each product
def generate_product_capacities(total_capacity):
    capacities = np.random.dirichlet(np.ones(len(products)), size=1)[0]
    return capacities * total_capacity

# Generate product capacities for each plant
plant_product_capacities = []

for _, plant in plants_df.iterrows():
    plant_capacities = generate_product_capacities(plant['Capacity'])
    for product, capacity in zip(products, plant_capacities):
        plant_product_capacities.append({
            'PlantID': f"PLANT_{plant['Pincode']}",
            'PlantName': plant['OfficeName'],
            'District': plant['District'],
            'StateName': plant['StateName'],
            'Latitude': plant['Latitude'],
            'Longitude': plant['Longitude'],
            'Product': product,
            'Capacity': round(capacity, 2)  # Rounded to 2 decimal places
        })

# Create a new DataFrame for plant product capacities
plant_product_df = pd.DataFrame(plant_product_capacities)

# Display summary statistics
print(plant_product_df.groupby('Product').agg({
    'Capacity': ['mean', 'min', 'max', 'sum']
}))

# Save to CSV
plant_product_df.to_csv('amul_plant_product_capacities.csv', index=False)

print("Amul plant product capacities have been generated and saved to 'amul_plant_product_capacities.csv'")

# Display the first few rows of the new DataFrame
print(plant_product_df.head(10))