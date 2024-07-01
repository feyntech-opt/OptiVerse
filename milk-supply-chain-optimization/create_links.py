import pandas as pd
import numpy as np
import json
from math import radians, sin, cos, sqrt, atan2

# Load the JSON data
with open('milk-supply-chain-optimization/data/amul-dairy-supply-chain-comprehensive-data.json', 'r') as f:
    json_data = json.load(f)

# Load the supply chain units data
units_df = pd.read_csv('milk-supply-chain-optimization/data/supply_chain_units.csv')

# Haversine formula to calculate distance between two points
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance

# Function to create links between two types of units within a specified range
def create_links(source_df, target_df, min_distance, max_distance):
    links = []
    for _, source in source_df.iterrows():
        for _, target in target_df.iterrows():
            distance = haversine_distance(source['Latitude'], source['Longitude'],
                                          target['Latitude'], target['Longitude'])
            if min_distance <= distance <= max_distance:
                links.append({
                    'SourceID': source['UnitID'],
                    'SourceType': source['UnitType'],
                    'TargetID': target['UnitID'],
                    'TargetType': target['UnitType'],
                    'Distance': distance
                })
    return links

# Create links for each type of connection
cooperatives = units_df[units_df['UnitType'] == 'VillageCooperative']
district_centers = units_df[units_df['UnitType'] == 'DistrictCenter']
plants = units_df[units_df['UnitType'] == 'Plant']
storage_units = units_df[units_df['UnitType'].isin(['BMC', 'ColdStorage', 'Warehouse'])]
retailers = units_df[units_df['UnitType'] == 'Retail']

# Get connection radii from JSON
coop_to_dc_range = json_data['connectionRadii']['villageCooperativesToDistrictCenters']
dc_to_plant_range = json_data['connectionRadii']['districtCentersToPlants']
plant_to_storage_range = json_data['connectionRadii']['plantsToStorageUnits']
storage_to_retail_range = json_data['connectionRadii']['storageUnitsToRetailCenters']

# Generate links
coop_to_dc_links = create_links(cooperatives, district_centers, coop_to_dc_range['min'], coop_to_dc_range['max'])
coop_to_plant_links = create_links(cooperatives, plants, coop_to_dc_range['min'], dc_to_plant_range['max'])
dc_to_plant_links = create_links(district_centers, plants, dc_to_plant_range['min'], dc_to_plant_range['max'])
plant_to_storage_links = create_links(plants, storage_units, plant_to_storage_range['min'], plant_to_storage_range['max'])
storage_to_retail_links = create_links(storage_units, retailers, storage_to_retail_range['min'], storage_to_retail_range['max'])
plant_to_retail_links = create_links(plants, retailers, storage_to_retail_range['min'], storage_to_retail_range['max'])

# Combine all links
all_links = (coop_to_dc_links + coop_to_plant_links + dc_to_plant_links +
             plant_to_storage_links + storage_to_retail_links + plant_to_retail_links)

# Convert to DataFrame and save to CSV
links_df = pd.DataFrame(all_links)
links_df.to_csv('milk-supply-chain-optimization/data/supply_chain_links.csv', index=False)

print(f"Total links generated: {len(all_links)}")
print("Supply chain links data saved to 'supply_chain_links.csv'")

# Display summary of links
link_types = links_df.groupby(['SourceType', 'TargetType']).size().reset_index(name='Count')
print("\nSummary of link types:")
print(link_types)