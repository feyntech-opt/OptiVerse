import numpy as np
import highspy as hs
h= hs.Highs()
inf = hs.kHighsInf
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import time
import warnings
from collections import defaultdict
warnings.simplefilter(action="ignore",category=FutureWarning)
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
with open('data/amul_data.json', 'r') as f:
    data = json.load(f)

arcs = pd.read_csv('data/arcs_new.csv')
units = pd.read_csv('data/units.csv')

validate_data(arcs, "arcs")
validate_data(units, "units")

capacity = units[units['Capacity'].notna()].set_index('UnitID')['Capacity'].to_dict()
storage_cost = units[units['StorageCostPerKg'].notna()].set_index('UnitID')['StorageCostPerKg'].to_dict()
distance = arcs.set_index(['SourceID', 'TargetID'])['Distance'].to_dict()
processing_cost = {product['name']: product['costs']['processing'] for product in data['products']}
              
milk_required = {product['name']: product['milkRequired'] for product in data['products']  }

shelf_life = {product['name']: product['shelfLife']['duration'] for product in data['products']}
units_type = units.set_index('UnitID')['UnitType'].to_dict()
transport_cost_per_km_kg = 0.01    

ARCS = list(zip(arcs['SourceID'], arcs['TargetID']))
UNITS = units['UnitID'].tolist()
PLANTS = units[units['UnitType'] == 'Plant']['UnitID'].tolist()
VILLAGE_COOPERATIVES =units[units['UnitType'] == 'VillageCooperative']['UnitID'].tolist()
RETAILS =units[units['UnitType']=='Retail']['UnitID'].tolist()
PRODUCTS = [product['name'] for product in data['products']]
            
DAIRY_PRODUCTS = [product for product in PRODUCTS ]

Intermediate_Units = units[(units["UnitType"] != "VillageCooperative") & (units["UnitType"] != "Retail")]['UnitID'].tolist()
STORAGE_UNITS = list(storage_cost.keys())
CAPACITY_UNITS = list(capacity.keys())
def solve_period(start_date, end_date):
    log_message(f"Solving for period: {start_date} to {end_date}")
    
    demand = pd.read_csv('data/demand_01.csv', parse_dates=['Date'])
    demand = demand[(demand['Date'] >= start_date) & (demand['Date'] <= end_date)]
    
    demand.loc[demand['Product'] == 'Ghee', 'Demand'] = demand.loc[demand['Product'] == 'Ghee', 'Demand'] / 30
    weekly_products = ["Ice Cream", "Cheese","Butter"]
    for wp in weekly_products:
       demand.loc[demand['Product'] == wp, 'Demand'] = demand.loc[demand['Product'] == wp, 'Demand'] / 7
      
   
    validate_data(demand, "demand")
    t= demand.index
    flow = {}
    storage={}
    production={}
    slack={}
    Big_M =1000000
    i =-1
     
    for arc in ARCS:
       for product in PRODUCTS:
        var_name = f"flow_{arc[0]}_{arc[1]}_{product}"
        flow[var_name] = h.addVariable(0, hs.kHighsInf, name=var_name)
        i+=1
    flow_end= i   
     
    for unit in STORAGE_UNITS:
       for product in PRODUCTS:
        var_name = f"storage_{unit}_{product}"
        storage[var_name] = h.addVariable(0, hs.kHighsInf, name=var_name)
        i+=1
    storage_end= i
     
    for plant in PLANTS:
       for dp in DAIRY_PRODUCTS:
        var_name = f"production_{plant}_{dp}"
        production[var_name] = h.addVariable(0, hs.kHighsInf, name=var_name)
        i+=1
    production_end =i
     
    for index in demand.index: 
        var_name = f"slack_{index}"
        slack[var_name] = h.addVariable(0, hs.kHighsInf, name=var_name)
        i+=1
       
     
    objtransport = sum(flow[f"flow_{i}_{j}_{p}"] * distance[i,j] * transport_cost_per_km_kg
                    for (i,j) in ARCS for p in PRODUCTS)
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+" - objtransport")
    
    objstorage= sum( storage[f"storage_{u}_{p}"] * storage_cost[u]  for u in STORAGE_UNITS for p in PRODUCTS)
    objproduction = sum( production[f"production_{p}_{dp}"] *  processing_cost [dp]   for  p in PLANTS for dp in DAIRY_PRODUCTS)
     
    objslack = sum(Big_M * slack[f"slack_{index}"]   for index  in demand.index)
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+" - object slack")
     
    for u in CAPACITY_UNITS: 
        h.addConstr(sum(  storage[f"storage_{u}_{p}"] for p in PRODUCTS) <= capacity[u])
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+" - capacity cnstr defined")
     
    for pl in PLANTS:
         
        h.addConstr(
            sum(production[f"production_{pl}_{dp}"] * milk_required[dp] for dp in PRODUCTS) <=
            sum(flow[f"flow_{i}_{j}_{'Milk'}"] for (i,j) in ARCS if j == pl)
        )
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+" - milk cnvrsn cnstr defined")
    
    for idx, row in demand.iterrows():
        u, p = row['Retail_Unit_ID'], row['Product']
        h.addConstr(
           sum( flow[f"flow_{i}_{u}_{p}"] for (i,j) in ARCS if j == u) +   
            slack[f"slack_{idx}"] >= row['Demand']*1000    #  its metric ton to kgs cnvrsn
        )
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+" - demand cnstr defined")
    
    for u in Intermediate_Units:
        for p in PRODUCTS:
         
            outflow = sum(flow[f"flow_{i}_{j}_{p}"] for (i,j) in ARCS if i == u)
            if u in PLANTS and p != 'Milk':
              
                h.addConstr(  production[f"production_{u}_{p}"] == outflow )
           
            elif u  not in   PLANTS  :
               inflow = sum( flow[f"flow_{i}_{j}_{p}"] for (i,j) in ARCS if j == u)
               h.addConstr(inflow == outflow + storage[f"storage_{u}_{p}"])  
               
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+"- conservation cnstr defined")
     
    h.minimize(objtransport +objproduction+objstorage+ objslack)
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+"obj defined")
    
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+ "- crossed check point")
    h.run()
    solution = h.getSolution()
    print("Optimal solution:", solution) 
    decision_vars = solution.col_value
     
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+"collection of solution as df started") 
     
    all_values= h.allVariableValues()
    all_names= h.allVariableNames()
    
    soln_dfs= pd.DataFrame({   "Variable" : all_names,
                                "Value"   : all_values  })
 
    flow_df= soln_dfs.loc[:flow_end]
    storage_df=soln_dfs.loc[flow_end+1 :storage_end]
    production_df= soln_dfs.loc[storage_end+1 : production_end]
    slack_df= soln_dfs.loc[production_end+1:]
    
    flow_df= flow_df[flow_df["Value"] !=0]
    storage_df= storage_df[storage_df["Value"]!=0]
    production_df= production_df[production_df["Value"] != 0]
    slack_df= slack_df[slack_df["Value"] != 0]

     

    excel_path = r"C:\\Users\\hp\\Downloads\\OR work\\AmulSCopt_Highys\\Solution_files\\Amul_1day_modelSoln3.xlsx"
    with pd.ExcelWriter(excel_path) as writer:
        flow_df.to_excel(writer, sheet_name="flow soln", index=False)
        storage_df.to_excel(writer, sheet_name="storage soln", index=False)
        production_df.to_excel(writer, sheet_name="production soln", index=False)
        slack_df.to_excel(writer, sheet_name="slack soln", index=False)

    
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+"Completed all tasks")
    print()   
start_date = datetime(2025, 1, 1)    
end_date = datetime(2025, 1, 1)
solve_period(start_date, end_date)   
