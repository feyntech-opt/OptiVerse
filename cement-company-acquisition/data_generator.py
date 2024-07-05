import pandas as pd
import numpy as np

# Company names
companies = ["Penna Cement", "Company B", "Company C"]

# Generating random data
np.random.seed(42)  # For reproducibility
data = {
    "Company": companies,
    "Market Share": np.random.uniform(10, 50, size=3),  # Market share in percentage
    "Revenue Growth": np.random.uniform(5, 20, size=3),  # Revenue growth in percentage
    "Production Capacity": np.random.uniform(
        1, 10, size=3
    ),  # Production capacity in million tons
    "Cost Structure": np.random.uniform(100, 500, size=3)
    * 10**7,  # Cost structure in million INR
    "Compliance Rating": np.random.uniform(
        1, 10, size=3
    ),  # Compliance rating out of 10
    "Market Regions": np.random.randint(1, 5, size=3),  # Number of market regions
    "Number of Plants": np.random.randint(1, 10, size=3),  # Number of plants
    "Integrated Plants": np.random.randint(1, 5, size=3),  # Number of integrated plants
    "Offer Price": np.random.uniform(1000, 2000, size=3)
    * 10**7,  # Offer price in million INR
}

# Creating DataFrame
df_companies = pd.DataFrame(data)

# Saving to CSV
df_companies.to_csv("cement-company-acquisition/companies_data_inr.csv", index=False)


# Hypothetical data for Adani
# Correcting the format of Cost Structure
adani_data = {
    "Company": ["Adani"],
    "Market Share": [30],  # Market share in percentage
    "Revenue Growth": [15],  # Revenue growth in percentage
    "Production Capacity": [8],  # Production capacity in million tons
    "Cost Structure": [300 * 10**7],  # Cost structure in INR
    "Compliance Rating": [8],  # Compliance rating out of 10
    "Market Regions": [3],  # Number of market regions
    "Number of Plants": [5],  # Number of plants
    "Integrated Plants": [2],  # Number of integrated plants
    "Offer Price": [1500 * 10**7],  # Offer price in INR (hypothetical)
}

# Creating DataFrame
df_adani = pd.DataFrame(adani_data)

# Saving to CSV
df_adani.to_csv("cement-company-acquisition/adani_data_inr.csv", index=False)
