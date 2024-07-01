import pandas as pd
import numpy as np
from scipy import interpolate

# Read the CSV file
df = pd.read_excel('milk-supply-chain-optimization/India pincode list.xlsx')

# Convert Latitude and Longitude to numeric, coercing errors to NaN
df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')

# Function to interpolate missing values
def interpolate_missing(series):
    # Get indices of non-NaN values
    valid = np.isfinite(series)
    # Get indices and values of non-NaN elements
    indices = np.arange(len(series))
    valid_indices = indices[valid]
    valid_values = series[valid]
    # Interpolate
    if len(valid_values) > 1:
        f = interpolate.interp1d(valid_indices, valid_values, kind='linear', fill_value='extrapolate')
        return f(indices)
    else:
        return series

# Group by CircleName, RegionName, DivisionName and interpolate within each group
for _, group in df.groupby(['CircleName', 'RegionName', 'DivisionName']):
    df.loc[group.index, 'Latitude'] = interpolate_missing(group['Latitude'])
    df.loc[group.index, 'Longitude'] = interpolate_missing(group['Longitude'])

# Save the updated DataFrame to a new CSV file
df.to_csv('milk-supply-chain-optimization/post_offices_interpolated.csv', index=False)

print("Interpolation complete. Results saved to 'post_offices_interpolated.csv'")