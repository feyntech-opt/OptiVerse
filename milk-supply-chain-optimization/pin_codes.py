import pandas as pd

# Load the provided CSV data
file_path = 'milk-supply-chain-optimization/India pincode list.xlsx'
df = pd.read_excel(file_path)

# Define the correct districts for each type of center based on actual Amul operations
districts_with_village_cooperatives = [
    'ANAND', 'KHEDA', 'SABAR KANTHA', 'BANAS KANTHA', 'GANDHINAGAR'
]
districts_with_district_centers = [
    'ANAND', 'KHEDA', 'SABAR KANTHA', 'BANAS KANTHA', 'GANDHINAGAR', 
    'VADODARA', 'RAJKOT', 'SURAT'
]
districts_with_plants = [
    'ANAND', 'GANDHINAGAR', 'RAJKOT', 'MUMBAI', 'PUNE', 
    'KOLKATA', 'INDORE', 'TIRUPATI', 'KHAMANON', 'GHAZIABAD'
]
districts_with_retail = [
    'ANAND', 'AHMEDABAD', 'SURAT', 'VADODARA', 'RAJKOT', 'MUMBAI', 
    'PUNE', 'DELHI', 'LUCKNOW', 'KANPUR', 'KOLKATA', 'CHENNAI', 
    'BANGALORE'
]

# Define districts for storage units
districts_with_bmcs = [
    'ANAND', 'KHEDA', 'SABAR KANTHA', 'BANAS KANTHA', 'GANDHINAGAR', 'PUNE', 'MUMBAI', 'KHAMANON', 'GHAZIABAD', 'KOLKATA', 'INDORE', 'TIRUPATI'
]
districts_with_cold_storage = [
    'ANAND', 'KHEDA', 'SABAR KANTHA', 'BANAS KANTHA', 'GANDHINAGAR', 'VADODARA', 'RAJKOT', 'SURAT', 'MUMBAI', 'PUNE', 'KHAMANON', 'GHAZIABAD', 'KOLKATA', 'INDORE', 'TIRUPATI'
]
districts_with_warehouses = [
    'ANAND', 'AHMEDABAD', 'SURAT', 'VADODARA', 'RAJKOT', 'MUMBAI', 'PUNE', 'DELHI', 'LUCKNOW', 'KANPUR', 'KOLKATA', 'CHENNAI', 'BANGALORE'
]

# Create new columns for each type of center
df['IsVillageCooperative'] = df['District'].isin(districts_with_village_cooperatives)
df['IsRetail'] = df['District'].isin(districts_with_retail)

# Filter for plants and district centers and take only the first and second rows within each district group
df['IsPlant'] = df.groupby('District').cumcount() < 2
df['IsPlant'] = df['IsPlant'] & df['District'].isin(districts_with_plants)

df['IsDistrictCenter'] = df.groupby('District').cumcount() < 2
df['IsDistrictCenter'] = df['IsDistrictCenter'] & df['District'].isin(districts_with_district_centers)

# Create new columns for storage units and take only the first and second rows within each district group
df['IsBMC'] = df.groupby('District').cumcount() < 2
df['IsBMC'] = df['IsBMC'] & df['District'].isin(districts_with_bmcs)

df['IsColdStorage'] = df.groupby('District').cumcount() < 2
df['IsColdStorage'] = df['IsColdStorage'] & df['District'].isin(districts_with_cold_storage)

df['IsWarehouse'] = df.groupby('District').cumcount() < 2
df['IsWarehouse'] = df['IsWarehouse'] & df['District'].isin(districts_with_warehouses)

# Save the updated dataframe to a new CSV file
output_file_path = 'milk-supply-chain-optimization/updated_India_pincode_list.csv'
df.to_csv(output_file_path, index=False)

# Display the count of each type of center and unique districts
village_count = df['IsVillageCooperative'].sum()
district_center_count = df['IsDistrictCenter'].sum()
plant_count = df['IsPlant'].sum()
retail_count = df['IsRetail'].sum()
bmc_count = df['IsBMC'].sum()
cold_storage_count = df['IsColdStorage'].sum()
warehouse_count = df['IsWarehouse'].sum()

unique_village_districts = df[df['IsVillageCooperative']]['District'].nunique()
unique_district_centers = df[df['IsDistrictCenter']]['District'].nunique()
unique_plant_districts = df[df['IsPlant']]['District'].nunique()
unique_retail_districts = df[df['IsRetail']]['District'].nunique()
unique_bmc_districts = df[df['IsBMC']]['District'].nunique()
unique_cold_storage_districts = df[df['IsColdStorage']]['District'].nunique()
unique_warehouse_districts = df[df['IsWarehouse']]['District'].nunique()

# Print the counts
print(f"Number of Village Cooperatives: {village_count}")
print(f"Number of District Centers: {district_center_count}")
print(f"Number of Plants: {plant_count}")
print(f"Number of Retail Centers: {retail_count}")
print(f"Number of Bulk Milk Coolers (BMCs): {bmc_count}")
print(f"Number of Cold Storage Units: {cold_storage_count}")
print(f"Number of Warehouses: {warehouse_count}")

print(f"Number of Unique Districts with Village Cooperatives: {unique_village_districts}")
print(f"Number of Unique Districts with District Centers: {unique_district_centers}")
print(f"Number of Unique Districts with Plants: {unique_plant_districts}")
print(f"Number of Unique Districts with Retail Centers: {unique_retail_districts}")
print(f"Number of Unique Districts with Bulk Milk Coolers (BMCs): {unique_bmc_districts}")
print(f"Number of Unique Districts with Cold Storage Units: {unique_cold_storage_districts}")
print(f"Number of Unique Districts with Warehouses: {unique_warehouse_districts}")
