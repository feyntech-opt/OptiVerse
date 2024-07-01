import pandas as pd
import random
import json

# Load the JSON data
with open('milk-supply-chain-optimization/data/amul-dairy-supply-chain-comprehensive-data.json', 'r') as f:
    json_data = json.load(f)

# Load the CSV data
df = pd.read_csv('milk-supply-chain-optimization/data/updated_India_pincode_list.csv')

# Function to generate random capacity
def generate_capacity(unit_type):
    if unit_type == 'BMC':
        return random.choice(json_data['infrastructureCosts']['bulkMilkCoolers']['typicalSizes'])
    elif unit_type == 'ColdStorage':
        min_cap = json_data['infrastructureCosts']['coldStorageUnits']['capacityRange']['min']
        max_cap = json_data['infrastructureCosts']['coldStorageUnits']['capacityRange']['max']
        return random.randint(min_cap, max_cap)
    elif unit_type == 'Warehouse':
        # Assuming warehouse capacity in tons, converting from the "Several thousand tons" description
        return random.randint(1000, 10000)
    elif unit_type in ['VillageCooperative', 'DistrictCenter']:
        # Using BMC capacity for these, as they likely have milk collection/storage
        min_cap = json_data['storageInfrastructure']['bulkMilkCoolers']['typicalCapacityRange']['min']
        max_cap = json_data['storageInfrastructure']['bulkMilkCoolers']['typicalCapacityRange']['max']
        return random.randint(min_cap, max_cap)
    else:
        return None  # For other types, capacity might not be applicable

# Function to calculate storage cost per kg
def calculate_storage_cost(unit_type, capacity):
    if unit_type in ['BMC', 'VillageCooperative', 'DistrictCenter']:
        return (json_data['infrastructureCosts']['bulkMilkCoolers']['costPer1000Liters'] / 1000) / capacity
    elif unit_type == 'ColdStorage':
        return json_data['infrastructureCosts']['coldStorageUnits']['costMediumSize'] / (capacity * 1000)  # Convert liters to kg
    elif unit_type == 'Warehouse':
        return json_data['infrastructureCosts']['warehouses']['costMediumSize'] / (capacity * 1000)  # Convert tons to kg
    else:
        return None

# Generate data for each type of unit
unit_data = []
unit_id = 1

for index, row in df.iterrows():
    for unit_type in ['VillageCooperative', 'Retail', 'Plant', 'DistrictCenter', 'BMC', 'ColdStorage', 'Warehouse']:
        if row[f'Is{unit_type}']:
            capacity = generate_capacity(unit_type)
            storage_cost = calculate_storage_cost(unit_type, capacity) if capacity else None
            unit_data.append({
                'UnitID': unit_id,
                'UnitType': unit_type,
                'Pincode': row['Pincode'],
                'District': row['District'],
                'State': row['StateName'],
                'Latitude': row['Latitude'],
                'Longitude': row['Longitude'],
                'Capacity': capacity,
                'CapacityUnit': 'liters' if unit_type in ['BMC', 'ColdStorage', 'VillageCooperative', 'DistrictCenter'] else 'tons' if unit_type == 'Warehouse' else None,
                'StorageCostPerKg': storage_cost
            })
            unit_id += 1

# Convert to DataFrame and save to CSV
unit_df = pd.DataFrame(unit_data)
unit_df.to_csv('milk-supply-chain-optimization/data/supply_chain_units.csv', index=False)

print("Supply chain unit data generated and saved to 'supply_chain_units.csv'")