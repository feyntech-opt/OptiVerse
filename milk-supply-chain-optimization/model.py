import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import numpy as np
import json
import os
from scipy.sparse import csr_matrix
from datetime import datetime, timedelta
import time


def log_message(message):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}")


log_message("Starting script execution")

# Load JSON data
log_message("Loading JSON data")
with open('data/input/amul_data.json', 'r') as f:
    data = json.load(f)

# Load CSV data
log_message("Loading CSV data")
arcs = pd.read_csv('data/input/arcs.csv')
units = pd.read_csv('data/input/units.csv')
demand = pd.read_csv('data/input/demand.csv')

log_message("Converting dates to datetime")
# Convert dates to datetime
demand['Date'] = pd.to_datetime(demand['Date'])

log_message("Creating Gurobi model")
# Create model
model = gp.Model("Amul_Supply_Chain_Optimization")

log_message("Defining sets")
# Sets
ARCS = list(zip(arcs['SourceID'], arcs['TargetID']))
UNITS = units['UnitID'].tolist()
PRODUCTS = [product['name'] for product in data['products']]
START_DATE = demand['Date'].min()
END_DATE = demand['Date'].max()
DATES = pd.date_range(START_DATE, END_DATE, freq='D')

log_message("Processing parameters")
# Parameters
capacity = units.set_index('UnitID')['Capacity'].to_dict()
storage_cost = units.set_index('UnitID')['StorageCostPerKg'].to_dict()
distance = arcs.set_index(['SourceID', 'TargetID'])['Distance'].to_dict()

processing_cost = {product['name']: product['costs']['processing'] for product in data['products']}
milk_required = {product['name']: product['milkRequired'] for product in data['products']}
shelf_life = {product['name']: product['shelfLife']['duration'] for product in data['products']}

transport_cost_per_km_kg = 0.01

log_message("Aggregating demand by week")
# Aggregate demand by week
demand['Week'] = demand['Date'].dt.to_period('W')
weekly_demand = demand.groupby(['Week', 'Retail_Unit_ID', 'Product'])['Demand'].sum().reset_index()
weekly_demand['Date'] = weekly_demand['Week'].dt.start_time

log_message("Creating decision variables")
# Create variables
flow = model.addVars(ARCS, PRODUCTS, DATES, name="flow", vtype=GRB.CONTINUOUS)
storage = model.addVars(UNITS, PRODUCTS, DATES, name="storage", vtype=GRB.CONTINUOUS)
production = model.addVars(UNITS, PRODUCTS, DATES, name="production", vtype=GRB.CONTINUOUS)
slack = model.addVars(weekly_demand.index, name="slack", vtype=GRB.CONTINUOUS)

log_message("Setting up objective function")
# Objective function components
obj_transport = gp.quicksum(flow[i, j, p, d] * distance[i, j] * transport_cost_per_km_kg
                            for (i, j) in ARCS for p in PRODUCTS for d in DATES)
obj_storage = gp.quicksum(storage[u, p, d] * storage_cost[u]
                          for u in UNITS if u in storage_cost for p in PRODUCTS for d in DATES)
obj_production = gp.quicksum(production[u, p, d] * processing_cost[p]
                             for u in UNITS for p in PRODUCTS for d in DATES)
obj_slack = gp.quicksum(1000000 * slack[idx] for idx in weekly_demand.index)

model.setObjective(obj_transport + obj_storage + obj_production + obj_slack, GRB.MINIMIZE)

log_message("Generating constraints")
# Prepare constraints
constraints = []

log_message("Generating flow conservation constraints")
# Flow conservation
for u in UNITS:
    for p in PRODUCTS:
        for d in DATES:
            inflow = gp.quicksum(flow[i, j, p, d] for (i, j) in ARCS if j == u)
            outflow = gp.quicksum(flow[i, j, p, d] for (i, j) in ARCS if i == u)
            if u in units[units['UnitType'] == 'Plant'].index:
                constraints.append((inflow + production[u, p, d] == outflow +
                                   storage[u, p, d], f"flow_cons_{u}_{p}_{d}"))
            else:
                prev_d = d - timedelta(days=1) if d > START_DATE else d
                constraints.append((inflow + storage[u, p, prev_d] == outflow +
                                   storage[u, p, d], f"flow_cons_{u}_{p}_{d}"))

log_message("Generating capacity constraints")
# Capacity constraints
for u in UNITS:
    if u in capacity:
        for d in DATES:
            constraints.append((gp.quicksum(storage[u, p, d] for p in PRODUCTS) <= capacity[u], f"capacity_{u}_{d}"))

log_message("Generating demand satisfaction constraints")
# Demand satisfaction (weekly)
for idx, row in weekly_demand.iterrows():
    u, p, d = row['Retail_Unit_ID'], row['Product'], row['Date']
    week_dates = pd.date_range(d, d + timedelta(days=6), freq='D')
    constraints.append((
        gp.quicksum(gp.quicksum(flow[i, u, p, wd] for (i, j) in ARCS if j == u) for wd in week_dates) +
        slack[idx] >= row['Demand'],
        f"demand_{u}_{p}_{d}"
    ))

log_message("Generating milk conversion constraints")
# Milk conversion in plants
for u in units[units['UnitType'] == 'Plant'].index:
    for d in DATES:
        constraints.append((
            gp.quicksum(production[u, p, d] * milk_required[p] for p in PRODUCTS) <=
            gp.quicksum(flow[i, u, 'Milk', d] for (i, j) in ARCS if j == u),
            f"milk_conv_{u}_{d}"
        ))

log_message("Generating shelf life constraints")
# Shelf life constraints
for u in UNITS:
    for p in PRODUCTS:
        for d in DATES:
            if d >= START_DATE + timedelta(days=shelf_life[p]):
                constraints.append((
                    storage[u, p, d] <= gp.quicksum(production[u, p, t]
                                                    for t in pd.date_range(d - timedelta(days=shelf_life[p]), d)),
                    f"shelf_life_{u}_{p}_{d}"
                ))

log_message("Adding constraints to the model")
# Add all constraints to the model
model.addConstrs(constraints)

log_message("Starting optimization")
# Solve the model
model.optimize()

log_message("Optimization complete. Preparing to save results.")

# Create output directory if it doesn't exist
os.makedirs('data/output', exist_ok=True)

# Save results to CSV files
if model.status == GRB.OPTIMAL:
    log_message("Optimal solution found")
    print('Total cost:', model.objVal)

    log_message("Saving flow data")
    # Save flow data
    flow_data = [(i, j, p, d, flow[i, j, p, d].x)
                 for (i, j) in ARCS for p in PRODUCTS for d in DATES if flow[i, j, p, d].x > 0]
    pd.DataFrame(flow_data, columns=['SourceID', 'TargetID', 'Product',
                 'Date', 'Amount']).to_csv('data/output/flow.csv', index=False)

    log_message("Saving storage data")
    # Save storage data
    storage_data = [(u, p, d, storage[u, p, d].x)
                    for u in UNITS for p in PRODUCTS for d in DATES if storage[u, p, d].x > 0]
    pd.DataFrame(storage_data, columns=['UnitID', 'Product', 'Date', 'Amount']
                 ).to_csv('data/output/storage.csv', index=False)

    log_message("Saving production data")
    # Save production data
    production_data = [(u, p, d, production[u, p, d].x)
                       for u in units[units['UnitType'] == 'Plant'].index
                       for p in PRODUCTS for d in DATES if production[u, p, d].x > 0]
    pd.DataFrame(production_data, columns=['PlantID', 'Product', 'Date', 'Amount']
                 ).to_csv('data/output/production.csv', index=False)

    log_message("Saving unmet demand data")
    # Save unmet demand data
    unmet_demand_data = [(weekly_demand.loc[idx, 'Date'], weekly_demand.loc[idx, 'Retail_Unit_ID'],
                          weekly_demand.loc[idx, 'Product'], slack[idx].x)
                         for idx in weekly_demand.index if slack[idx].x > 0]
    pd.DataFrame(unmet_demand_data, columns=['Date', 'RetailUnitID', 'Product',
                 'UnmetDemand']).to_csv('data/output/unmet_demand.csv', index=False)

    log_message("Results saved to CSV files in data/output folder")
else:
    log_message("No optimal solution found")

log_message("Script execution completed")
