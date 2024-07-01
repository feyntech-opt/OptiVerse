# Amul Dairy Supply Chain Model

## Project Overview
This project aims to create a comprehensive model of Amul's dairy supply chain, focusing on end-to-end operations from milk collection to product distribution. The model is designed to represent 5% of India's projected milk demand for 2025, providing insights into costs, logistics, and inventory management across the supply chain.

## Approach

### 1. Data Collection and Structuring
- Gathered data on various dairy products, including production costs, processing details, and packaging options.
- Collected information on supply chain infrastructure, transportation costs, and operational parameters.
- Structured data in a JSON format for easy access and manipulation.

### 2. Product Lifecycle Modeling
- Defined detailed product information including:
  - Raw material requirements
  - Processing costs and methods
  - Packaging options with associated costs and market shares
  - Shelf life and storage conditions
  - Maximum time allowed at retailers

### 3. Supply Chain Network Modeling
- Defined different types of facilities in the supply chain:
  - Village cooperatives
  - District centers
  - Processing plants
  - Storage facilities (BMC, Cold Storage, Warehouses)
  - Retail centers
- Established connection radii between different types of facilities to represent realistic transportation links.

### 4. Cost Analysis
- Broke down costs for each stage of the supply chain:
  - Raw material procurement
  - Transportation
  - Processing
  - Storage
  - Packaging

### 5. Transportation Network Creation
We've implemented a Python script to create a network of transportation links between different facilities in the supply chain. Here's an overview of the approach:

a. Data Loading:
   - Load CSV files containing information about each type of facility (cooperatives, district centers, plants, storage facilities, retail centers).

b. Distance Calculation:
   - Implement the Haversine formula to calculate the distance between two geographic coordinates.

c. Link Creation:
   - Define a function `create_links` that generates links between facilities based on their type and a maximum distance threshold.
   - Create links for different segments of the supply chain (e.g., cooperatives to district centers, district centers to plants, etc.).

d. Data Compilation and Export:
   - Combine all generated links into a single dataset.
   - Export the links data to a CSV file for further analysis or visualization.

## Usage Instructions

1. Data Preparation:
   - Ensure all facility data is prepared in CSV format with required columns (ID, latitude, longitude, Districtname).
   - Update file paths in the Python script to point to your data files.

2. Running the Script:
   - Execute the Python script to generate the transportation links.
   - The script will output a CSV file containing all the generated links.

3. Data Analysis:
   - Use the generated JSON data (product information, costs, etc.) and the transportation links CSV for further analysis, optimization, or visualization of the supply chain.

## Future Enhancements
- Implement demand forecasting models.
- Develop optimization algorithms for route planning and inventory management.
- Create visualization tools for the supply chain network.
- Integrate real-time data feeds for dynamic supply chain management.

## Notes
- All monetary values are in Indian Rupees (INR).
- The model is based on estimations and may not reflect exact real-world costs or conditions.
- Regular updates to the data are recommended to maintain the model's accuracy and relevance.

