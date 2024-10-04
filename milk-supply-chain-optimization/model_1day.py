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

arcs = pd.read_csv('data/arcs.csv')
units = pd.read_csv('data/units.csv')

validate_data(arcs, "arcs")
validate_data(units, "units")
# Process parameters
capacity = units[units['Capacity'].notna()].set_index('UnitID')['Capacity'].to_dict()
storage_cost = units[units['StorageCostPerKg'].notna()].set_index('UnitID')['StorageCostPerKg'].to_dict()
distance = arcs.set_index(['SourceID', 'TargetID'])['Distance'].to_dict()
processing_cost = {product['name']: product['costs']['processing'] for product in data['products']}
                 #milk_required = {product['name']: product['milkRequired'] for product in data['products'] if product['name'] != 'Milk'}
milk_required = {product['name']: product['milkRequired'] for product in data['products']  }

shelf_life = {product['name']: product['shelfLife']['duration'] for product in data['products']}
units_type = units.set_index('UnitID')['UnitType'].to_dict()
transport_cost_per_km_kg = 0.01    
#region Sets
ARCS = list(zip(arcs['SourceID'], arcs['TargetID']))
UNITS = units['UnitID'].tolist()
PLANTS = units[units['UnitType'] == 'Plant']['UnitID'].tolist()
VILLAGE_COOPERATIVES =units[units['UnitType'] == 'VillageCooperative']['UnitID'].tolist()
RETAILS =units[units['UnitType']=='Retail']['UnitID'].tolist()
PRODUCTS = [product['name'] for product in data['products']]
             #DAIRY_PRODUCTS = [product for product in PRODUCTS if product != 'Milk']
DAIRY_PRODUCTS = [product for product in PRODUCTS ]

Intermediate_Units = units[(units["UnitType"] != "VillageCooperative") & (units["UnitType"] != "Retail")]['UnitID'].tolist()
STORAGE_UNITS = list(storage_cost.keys())
CAPACITY_UNITS = list(capacity.keys())
#endregion
def solve_period(start_date, end_date):
    log_message(f"Solving for period: {start_date} to {end_date}")
    
    demand = pd.read_csv('data/demand_01.csv', parse_dates=['Date'])
    demand = demand[(demand['Date'] >= start_date) & (demand['Date'] <= end_date)]
    # we need to transform all demands as a daily limits
    demand.loc[demand['Product'] == 'Ghee', 'Demand'] = demand.loc[demand['Product'] == 'Ghee', 'Demand'] / 30
    weekly_products = ["Ice Cream", "Cheese","Butter"]
    for wp in weekly_products:
       demand.loc[demand['Product'] == wp, 'Demand'] = demand.loc[demand['Product'] == wp, 'Demand'] / 7
      
   
    validate_data(demand, "demand")
    t= demand.index
    #model = hs.Model("Amul_Supply_Chain_Optimization")
    flow = {}
    storage={}
    production={}
    slack={}
    Big_M =1000000
    #region break points of variables
    i =-1
    #endregion
    #region variables definying
    for arc in ARCS:
       for product in PRODUCTS:
        var_name = f"flow_{arc[0]}_{arc[1]}_{product}"
        flow[var_name] = h.addVariable(0, hs.kHighsInf, name=var_name)
        i+=1
    flow_end= i   
    # storage = model.addVars(UNITS, PRODUCTS, name="storage")
    for unit in STORAGE_UNITS:
       for product in PRODUCTS:
        var_name = f"storage_{unit}_{product}"
        storage[var_name] = h.addVariable(0, hs.kHighsInf, name=var_name)
        i+=1
    storage_end= i
    #production = model.addVars(PLANTS, DAIRY_PRODUCTS, name="production")
    for plant in PLANTS:
       for dp in DAIRY_PRODUCTS:
        var_name = f"production_{plant}_{dp}"
        production[var_name] = h.addVariable(0, hs.kHighsInf, name=var_name)
        i+=1
    production_end =i
    # slack = model.addVars(demand.index, name="slack")
    for index in demand.index: 
        var_name = f"slack_{index}"
        slack[var_name] = h.addVariable(0, hs.kHighsInf, name=var_name)
        i+=1
       
    #endregion
    #region Objective function Terms
    objtransport = sum(flow[f"flow_{i}_{j}_{p}"] * distance[i,j] * transport_cost_per_km_kg
                    for (i,j) in ARCS for p in PRODUCTS)
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+" - objtransport")
    #obj_storage = gp.quicksum(storage[u,p] * storage_cost[u] for u in STORAGE_UNITS for p in PRODUCTS)

    objstorage= sum( storage[f"storage_{u}_{p}"] * storage_cost[u]  for u in STORAGE_UNITS for p in PRODUCTS)
    #obj_production = gp.quicksum(production[u,p] * processing_cost[p] for u in PLANTS for p in DAIRY_PRODUCTS)
    objproduction = sum( production[f"production_{p}_{dp}"] *  processing_cost [dp]   for  p in PLANTS for dp in DAIRY_PRODUCTS)
    #obj_slack = gp.quicksum(1000000 * slack[idx] for idx in demand.index)
    objslack = sum(Big_M * slack[f"slack_{index}"]   for index  in demand.index)
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+" - object slack")
    #endregion
    #h.minimize(objtransport +objproduction+objstorage+ objslack)
    # print("object defined")

    #region constarints defining
    # capacity constaraint
    for u in CAPACITY_UNITS: 
        h.addConstr(sum(  storage[f"storage_{u}_{p}"] for p in PRODUCTS) <= capacity[u])
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+" - capacity cnstr defined")
    # milk conversion in plants
    for pl in PLANTS:
        #we need to add outflow of milk???
        h.addConstr(
            sum(production[f"production_{pl}_{dp}"] * milk_required[dp] for dp in PRODUCTS) <=
            sum(flow[f"flow_{i}_{j}_{'Milk'}"] for (i,j) in ARCS if j == pl)
        )
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+" - milk cnvrsn cnstr defined")
    # demand constraint at retail
    for idx, row in demand.iterrows():
        u, p = row['Retail_Unit_ID'], row['Product']
        h.addConstr(
           sum( flow[f"flow_{i}_{u}_{p}"] for (i,j) in ARCS if j == u) +   
            slack[f"slack_{idx}"] >= row['Demand']*1000    #  its metric ton to kgs cnvrsn
        )
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+" - demand cnstr defined")
    # flow conservation   constraint
    for u in Intermediate_Units:
        for p in PRODUCTS:
         #   inflow = sum( flow[f"flow_{i}_{j}_{p}"] for (i,j) in ARCS if j == u)
            outflow = sum(flow[f"flow_{i}_{j}_{p}"] for (i,j) in ARCS if i == u)
            if u in PLANTS and p != 'Milk':
              #  h.addConstr(inflow +  production[f"production_{u}_{p}"] == outflow +  storage[f"storage_{u}_{p}"])
                h.addConstr(  production[f"production_{u}_{p}"] == outflow )
           
            elif u  not in   PLANTS  :
               inflow = sum( flow[f"flow_{i}_{j}_{p}"] for (i,j) in ARCS if j == u)
               h.addConstr(inflow == outflow + storage[f"storage_{u}_{p}"])  
               
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+"- conservation cnstr defined")
    #endregion
    h.minimize(objtransport +objproduction+objstorage+ objslack)
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+"obj defined")
    #h.writeModel("model_1day.lp")
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+ "- crossed check point")
    h.run()
    solution = h.getSolution()
    print("Optimal solution:", solution) 
    decision_vars = solution.col_value
   # decision_var_names = h.getCols().col_names     
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+"collection of solution as df started") 
    #region new way of soln collection
    all_values= h.allVariableValues()
    all_names= h.allVariableNames()
    #soln_dict =dict(zip(all_names,all_values))
    soln_dfs= pd.DataFrame({   "Variable" : all_names,
                                "Value"   : all_values  })
    #region commented
    #categories = defaultdict(dict) 
    #for key, value in soln_dict.items():
     #prefix = key.split('_')[0]
     #categories[prefix][key] = value
    #soln_dfs = {prefix: pd.DataFrame(list(data.items()), columns=['Key', 'Value']).query('Value != 0') 
               # for prefix, data in categories.items()} 
    #endregion 
    #df = pd.DataFrame.from_dict(soln_dict, orient='index', columns=['variable', 'value'])
    flow_df= soln_dfs.loc[:flow_end]
    storage_df=soln_dfs.loc[flow_end+1 :storage_end]
    production_df= soln_dfs.loc[storage_end+1 : production_end]
    slack_df= soln_dfs.loc[production_end+1:]
    #region removing all  rows with variables with zero values
    flow_df= flow_df[flow_df["Value"] !=0]
    storage_df= storage_df[storage_df["Value"]!=0]
    production_df= production_df[production_df["Value"] != 0]
    slack_df= slack_df[slack_df["Value"] != 0]

    #endregion

    excel_path = r"C:\\Users\\hp\\Downloads\\OR work\\AmulSCopt_Highys\\Solution_files\\Amul_1day_modelSoln3.xlsx"
    with pd.ExcelWriter(excel_path) as writer:
        flow_df.to_excel(writer, sheet_name="flow soln", index=False)
        storage_df.to_excel(writer, sheet_name="storage soln", index=False)
        production_df.to_excel(writer, sheet_name="production soln", index=False)
        slack_df.to_excel(writer, sheet_name="slack soln", index=False)

    #endregion 
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}"+"Completed all tasks")
    print()   
start_date = datetime(2025, 1, 1)   # for a single  day
end_date = datetime(2025, 1, 1)
solve_period(start_date, end_date)   
