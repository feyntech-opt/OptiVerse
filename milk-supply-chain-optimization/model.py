import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import time

def log_message(message):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}")

def validate_data(df, name):
    log_message(f"Validating {name}")
    
    null_counts = df.isnull().sum()
    if null_counts.any():
        log_message(f"Warning: {name} contains null values:\n{null_counts[null_counts > 0]}")
    
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    for col in numeric_columns:
        inf_count = np.isinf(df[col]).sum()
        if inf_count > 0:
            log_message(f"Warning: Column '{col}' in {name} contains {inf_count} infinite values")
        if (df[col] == 0).all():
            log_message(f"Warning: Column '{col}' in {name} contains all zero values")
    
    for col, dtype in df.dtypes.items():
        log_message(f"Column '{col}' has data type: {dtype}")
    
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        log_message(f"Warning: {name} contains {duplicates} duplicate rows")
    
    log_message(f"Validation of {name} complete")

log_message("Starting script execution")

# Load data
with open('data/input/amul_data.json', 'r') as f:
    data = json.load(f)

arcs = pd.read_csv('data/input/arcs.csv')
units = pd.read_csv('data/input/units.csv')

validate_data(arcs, "arcs")
validate_data(units, "units")

# Process parameters
capacity = units[units['Capacity'].notna()].set_index('UnitID')['Capacity'].to_dict()
storage_cost = units[units['StorageCostPerKg'].notna()].set_index('UnitID')['StorageCostPerKg'].to_dict()
distance = arcs.set_index(['SourceID', 'TargetID'])['Distance'].to_dict()

processing_cost = {product['name']: product['costs']['processing'] for product in data['products']}
milk_required = {product['name']: product['milkRequired'] for product in data['products'] if product['name'] != 'Milk'}
shelf_life = {product['name']: product['shelfLife']['duration'] for product in data['products']}

transport_cost_per_km_kg = 0.01

# Sets
ARCS = list(zip(arcs['SourceID'], arcs['TargetID']))
UNITS = units['UnitID'].tolist()
PLANTS = units[units['UnitType'] == 'Plant']['UnitID'].tolist()
PRODUCTS = [product['name'] for product in data['products']]
DAIRY_PRODUCTS = [product for product in PRODUCTS if product != 'Milk']
STORAGE_UNITS = list(storage_cost.keys())
CAPACITY_UNITS = list(capacity.keys())

def solve_period(start_date, end_date):
    log_message(f"Solving for period: {start_date} to {end_date}")
    
    demand = pd.read_csv('data/input/demand.csv', parse_dates=['Date'])
    demand = demand[(demand['Date'] >= start_date) & (demand['Date'] <= end_date)]
    validate_data(demand, "demand")
    
    model = gp.Model("Amul_Supply_Chain_Optimization")
    
    # Create variables
    flow = model.addVars(ARCS, PRODUCTS, name="flow")
    storage = model.addVars(UNITS, PRODUCTS, name="storage")
    production = model.addVars(PLANTS, DAIRY_PRODUCTS, name="production")
    slack = model.addVars(demand.index, name="slack")
    
    # Objective function
    obj_transport = gp.quicksum(flow[i,j,p] * distance[i,j] * transport_cost_per_km_kg
                    for (i,j) in ARCS for p in PRODUCTS)
    obj_storage = gp.quicksum(storage[u,p] * storage_cost[u] 
                    for u in STORAGE_UNITS for p in PRODUCTS)
    obj_production = gp.quicksum(production[u,p] * processing_cost[p]
                    for u in PLANTS for p in DAIRY_PRODUCTS)
    obj_slack = gp.quicksum(1000000 * slack[idx] for idx in demand.index)
    
    model.setObjective(obj_transport + obj_storage + obj_production + obj_slack, GRB.MINIMIZE)
    
    # Constraints
    # Flow conservation
    for u in UNITS:
        for p in PRODUCTS:
            inflow = gp.quicksum(flow[i,j,p] for (i,j) in ARCS if j == u)
            outflow = gp.quicksum(flow[i,j,p] for (i,j) in ARCS if i == u)
            if u in PLANTS and p != 'Milk':
                model.addConstr(inflow + production[u,p] == outflow + storage[u,p])
            else:
                model.addConstr(inflow == outflow + storage[u,p])
    
    # Capacity constraints (only for units with defined capacity)
    for u in CAPACITY_UNITS:
        model.addConstr(gp.quicksum(storage[u,p] for p in PRODUCTS) <= capacity[u])
    
    # Demand satisfaction
    for idx, row in demand.iterrows():
        u, p = row['Retail_Unit_ID'], row['Product']
        model.addConstr(
            gp.quicksum(flow[i,u,p] for (i,j) in ARCS if j == u) + 
            slack[idx] >= row['Demand']
        )
    
    # Milk conversion in plants
    for u in PLANTS:
        model.addConstr(
            gp.quicksum(production[u,p] * milk_required[p] for p in DAIRY_PRODUCTS) <=
            gp.quicksum(flow[i,u,'Milk'] for (i,j) in ARCS if j == u)
        )
    
    # Solve the model
    model.optimize()
    
    # Return results
    if model.status == GRB.OPTIMAL:
        flow_data = [(i, j, p, flow[i,j,p].x) for (i,j) in ARCS for p in PRODUCTS if flow[i,j,p].x > 0]
        storage_data = [(u, p, storage[u,p].x) for u in UNITS for p in PRODUCTS if storage[u,p].x > 0]
        production_data = [(u, p, production[u,p].x) for u in PLANTS for p in DAIRY_PRODUCTS if production[u,p].x > 0]
        unmet_demand_data = [(demand.loc[idx, 'Date'], demand.loc[idx, 'Retail_Unit_ID'], demand.loc[idx, 'Product'], slack[idx].x) for idx in demand.index if slack[idx].x > 0]
        return model.objVal, flow_data, storage_data, production_data, unmet_demand_data
    else:
        log_message(f"Optimization failed with status: {model.status}")
        return None, None, None, None, None

# Solve the problem using a rolling horizon approach
start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 12, 31)
period_length = timedelta(days=2)  # Solve for one week at a time

all_flow_data = []
all_storage_data = []
all_production_data = []
all_unmet_demand_data = []
total_cost = 0

while start_date <= end_date:
    period_end = min(start_date + period_length, end_date)
    
    cost, flow, storage, production, unmet_demand = solve_period(start_date, period_end)
    
    if cost is not None:
        total_cost += cost
        all_flow_data.extend([(start_date, *item) for item in flow])
        all_storage_data.extend([(start_date, *item) for item in storage])
        all_production_data.extend([(start_date, *item) for item in production])
        all_unmet_demand_data.extend(unmet_demand)
    else:
        log_message(f"Failed to find optimal solution for period: {start_date} to {period_end}")
    
    start_date = period_end + timedelta(days=1)

# Save results
log_message("Saving results")
os.makedirs('data/output', exist_ok=True)

pd.DataFrame(all_flow_data, columns=['Date', 'SourceID', 'TargetID', 'Product', 'Amount']).to_csv('data/output/flow.csv', index=False)
pd.DataFrame(all_storage_data, columns=['Date', 'UnitID', 'Product', 'Amount']).to_csv('data/output/storage.csv', index=False)
pd.DataFrame(all_production_data, columns=['Date', 'PlantID', 'Product', 'Amount']).to_csv('data/output/production.csv', index=False)
pd.DataFrame(all_unmet_demand_data, columns=['Date', 'RetailUnitID', 'Product', 'UnmetDemand']).to_csv('data/output/unmet_demand.csv', index=False)

log_message(f"Optimization complete. Total cost: {total_cost}")
log_message("Script execution completed")