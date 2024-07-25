from datetime import datetime
from importlib import metadata
from logging.handlers import RotatingFileHandler
import os
import re
import sys
import pulp
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, Table, Column, Integer, Float, MetaData, select
from sqlalchemy.orm import sessionmaker
import logging
import time
import traceback


def setup_logging(log_dir='logs'):
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create a unique log file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f'dolo650_optimization_{timestamp}.log')

    # Set up logging configuration
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    # Create a logger
    logger = logging.getLogger()

    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)

    # Create formatters and add it to handlers
    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(log_format)
    file_handler.setFormatter(log_format)

    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# Database connection
engine = create_engine('sqlite:///dolo_650_supply_chain.db', echo=False)
sql_metadata = MetaData()  # Renamed from 'metadata' to 'sql_metadata'
Session = sessionmaker(bind=engine)


def fetch_data(query):
    return pd.read_sql(query, engine)

def optimize_supply_chain():
    start_time = time.time()
    logger.info("Starting fast-build supply chain model construction with PuLP")

    # Fetch data
    facilities_df = fetch_data("SELECT * FROM facility")
    products_df = fetch_data("SELECT * FROM product")
    suppliers_df = fetch_data("SELECT * FROM supplier")
    supplier_products_df = fetch_data("SELECT * FROM supplier_product")
    post_offices_df = fetch_data("SELECT * FROM post_office")
    transportation_links_df = fetch_data("SELECT * FROM transportation_link")

    logger.info(f"Data fetching completed. Time taken: {time.time() - start_time:.2f} seconds")

    # Data preprocessing
    products_df['IsRawMaterial'] = products_df['IsRawMaterial'].astype(bool)
    
    # Create efficient data structures
    facilities = facilities_df.FacilityID.tolist()
    products = products_df.ProductID.tolist()
    suppliers = suppliers_df.SupplierID.tolist()
    post_offices = post_offices_df.PostOfficeID.tolist()
    raw_materials = products_df[products_df.IsRawMaterial].ProductID.tolist()
    finished_products = products_df[~products_df.IsRawMaterial].ProductID.tolist()

    facility_capacities = dict(zip(facilities_df.FacilityID, facilities_df.MaxCapacity))
    product_prices = dict(zip(products_df.ProductID, products_df.PricePerUnit))
    manufacturing_costs = dict(zip(facilities_df.FacilityID, facilities_df.ManufacturingCostMax))
    post_office_demands = dict(zip(post_offices_df.PostOfficeID, post_offices_df.DoloDemandMin))
    conversion_factors = dict(zip(products_df.ProductID, products_df.ConversionFactor))
    
    supplier_product_costs = {
        (row.SupplierID, row.ProductID): row.Cost 
        for _, row in supplier_products_df.iterrows()
    }
    
    transport_links = {
        (row.FromFacilityID, row.ToPostOfficeID): row.TotalCost 
        for _, row in transportation_links_df.iterrows()
    }

    logger.info(f"Data preprocessing completed. Time taken: {time.time() - start_time:.2f} seconds")

    # Create PuLP model
    model = pulp.LpProblem("Dolo650_Supply_Chain", pulp.LpMaximize)

    # Define variables
    production = pulp.LpVariable.dicts("Production", 
                                       ((f, p) for f in facilities for p in finished_products),
                                       lowBound=0,
                                       cat='Continuous')
    
    sourcing = pulp.LpVariable.dicts("Sourcing",
                                     ((s, p, f) for s in suppliers for p in raw_materials for f in facilities),
                                     lowBound=0,
                                     cat='Continuous')
    
    distribution = pulp.LpVariable.dicts("Distribution",
                                         ((f, po) for f in facilities for po in post_offices),
                                         lowBound=0,
                                         cat='Continuous')

    logger.info(f"Variables defined. Time taken: {time.time() - start_time:.2f} seconds")

    # Objective function
    model += (
        pulp.lpSum(distribution[f, po] * product_prices[finished_products[0]]
                   for f in facilities for po in post_offices) -
        pulp.lpSum(sourcing[s, p, f] * supplier_product_costs.get((s, p), 0)
                   for s in suppliers for p in raw_materials for f in facilities) -
        pulp.lpSum(production[f, p] * manufacturing_costs[f]
                   for f in facilities for p in finished_products) -
        pulp.lpSum(distribution[f, po] * transport_links.get((f, po), 0)
                   for f in facilities for po in post_offices)
    )

    logger.info(f"Objective function defined. Time taken: {time.time() - start_time:.2f} seconds")

    # Constraints
    # Production capacity constraints
    for f in facilities:
        model += pulp.lpSum(production[f, p] for p in finished_products) <= facility_capacities[f]

    # Raw material balance constraints
    for f in facilities:
        for p in raw_materials:
            model += (pulp.lpSum(sourcing[s, p, f] for s in suppliers) ==
                      pulp.lpSum(production[f, fp] * conversion_factors[p] for fp in finished_products))

    # Demand satisfaction constraints
    for po in post_offices:
        model += pulp.lpSum(distribution[f, po] for f in facilities) >= post_office_demands[po]

    # Production-distribution balance constraint
    model += (pulp.lpSum(production[f, p] for f in facilities for p in finished_products) ==
              pulp.lpSum(distribution[f, po] for f in facilities for po in post_offices))

    logger.info(f"Constraints defined. Time taken: {time.time() - start_time:.2f} seconds")
    logger.info(f"Model building completed. Total time taken: {time.time() - start_time:.2f} seconds")

    return model

def solve_model(model, solver_name='CBC'):
    start_time = time.time()
    logger.info(f"Starting optimization with {solver_name}")

    if solver_name.upper() == 'CBC':
        solver = pulp.PULP_CBC_CMD(msg=True, timeLimit=600)
    elif solver_name.upper() == 'GUROBI':
        solver = pulp.GUROBI_CMD(msg=True, timeLimit=600)
    elif solver_name.upper() == 'CPLEX':
        solver = pulp.CPLEX_CMD(msg=True, timelimit=600)
    else:
        logger.error(f"Unsupported solver: {solver_name}")
        return None

    result = model.solve(solver)

    logger.info(f"Optimization completed. Time taken: {time.time() - start_time:.2f} seconds")
    logger.info(f"Status: {pulp.LpStatus[model.status]}")
    logger.info(f"Objective Value: {pulp.value(model.objective)}")

    return result

def safe_int_convert(value):
    # Remove any non-digit characters and convert to int
    return int(''.join(filter(str.isdigit, value)))

def extract_solution(model):
    production = []
    sourcing = []
    distribution = []

    for v in model.variables():
        if v.varValue > 0:
            # Use regex to find all numbers in the variable name
            numbers = re.findall(r'\d+', v.name)
            
            if v.name.startswith("Production"):
                production.append({
                    'FacilityID': safe_int_convert(numbers[0]),
                    'ProductID': safe_int_convert(numbers[1]),
                    'Value': v.varValue
                })
            elif v.name.startswith("Sourcing"):
                sourcing.append({
                    'SupplierID': safe_int_convert(numbers[0]),
                    'ProductID': safe_int_convert(numbers[1]),
                    'FacilityID': safe_int_convert(numbers[2]),
                    'Value': v.varValue
                })
            elif v.name.startswith("Distribution"):
                distribution.append({
                    'FacilityID': safe_int_convert(numbers[0]),
                    'PostOfficeID': safe_int_convert(numbers[1]),
                    'Value': v.varValue
                })

    production_df = pd.DataFrame(production)
    sourcing_df = pd.DataFrame(sourcing)
    distribution_df = pd.DataFrame(distribution)

    return production_df, sourcing_df, distribution_df

def clean_id_column(value):
    if isinstance(value, str) and value.startswith('(') and value.endswith(')'):
        try:
            return ast.literal_eval(value)[0]
        except:
            return value
    return value

def clean_dataframe(df):
    for col in df.columns:
        if col.endswith('ID'):
            df[col] = df[col].apply(clean_id_column)
    return df

def debug_dataframe(df, name):
    logger.info(f"Debugging DataFrame: {name}")
    logger.info(f"Shape: {df.shape}")
    logger.info(f"Columns: {df.columns}")
    logger.info(f"Data types:\n{df.dtypes}")
    logger.info(f"First few rows:\n{df.head().to_string()}")


def push_solution_to_db(production, sourcing, distribution):
    debug_dataframe(production, "Production (before push)")
    debug_dataframe(sourcing, "Sourcing (before push)")
    debug_dataframe(distribution, "Distribution (before push)")

    # Create tables if they don't exist
    production_table = Table('production_solution', sql_metadata,
                             Column('FacilityID', Integer),
                             Column('ProductID', Integer),
                             Column('Value', Float))
    
    sourcing_table = Table('sourcing_solution', sql_metadata,
                           Column('SupplierID', Integer),
                           Column('ProductID', Integer),
                           Column('FacilityID', Integer),
                           Column('Value', Float))
    
    distribution_table = Table('distribution_solution', sql_metadata,
                               Column('FacilityID', Integer),
                               Column('PostOfficeID', Integer),
                               Column('Value', Float))
    
    sql_metadata.create_all(engine)
    
    session = Session()
    try:
        # Clear existing data
        session.execute(production_table.delete())
        session.execute(sourcing_table.delete())
        session.execute(distribution_table.delete())
        
        # Insert new data
        session.execute(production_table.insert(), production.to_dict('records'))
        session.execute(sourcing_table.insert(), sourcing.to_dict('records'))
        session.execute(distribution_table.insert(), distribution.to_dict('records'))
        
        # Commit the changes
        session.commit()
        logger.info("Solution data pushed to database successfully.")
        
        # Verify the data insertion
        verify_data_insertion(session, production_table, sourcing_table, distribution_table)
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error pushing data to database: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        session.close()

def verify_data_insertion(session, production_table, sourcing_table, distribution_table):
    production_count = session.query(production_table).count()
    sourcing_count = session.query(sourcing_table).count()
    distribution_count = session.query(distribution_table).count()
    
    logger.info(f"Verification - Records in production_solution: {production_count}")
    logger.info(f"Verification - Records in sourcing_solution: {sourcing_count}")
    logger.info(f"Verification - Records in distribution_solution: {distribution_count}")
    
    if production_count == 0 or sourcing_count == 0 or distribution_count == 0:
        logger.warning("One or more solution tables are empty after insertion!")

def fetch_solution_from_db():
    try:
        production = pd.read_sql_table('production_solution', engine)
        sourcing = pd.read_sql_table('sourcing_solution', engine)
        distribution = pd.read_sql_table('distribution_solution', engine)

        debug_dataframe(production, "Production (after fetch)")
        debug_dataframe(sourcing, "Sourcing (after fetch)")
        debug_dataframe(distribution, "Distribution (after fetch)")

        return production, sourcing, distribution
    except Exception as e:
        logger.error(f"Error fetching data from database: {str(e)}")
        logger.error(traceback.format_exc())
        return None, None, None
    
def validate_solution(production, sourcing, distribution, facilities_df, products_df, suppliers_df, post_offices_df):
    validation_results = []

    # Log DataFrame information
    for df_name, df in [("production", production), ("sourcing", sourcing), ("distribution", distribution), 
                        ("facilities_df", facilities_df), ("products_df", products_df), 
                        ("suppliers_df", suppliers_df), ("post_offices_df", post_offices_df)]:
        logger.info(f"{df_name} DataFrame:")
        logger.info(f"  Shape: {df.shape}")
        logger.info(f"  Columns: {df.columns.tolist()}")
        logger.info(f"  Index: {df.index}")
        logger.info(f"  Data types:\n{df.dtypes}")
        logger.info(f"  First few rows:\n{df.head().to_string()}")
        logger.info("---")

    # Check production capacity constraints
    production_by_facility = production.groupby('FacilityID')['Value'].sum()
    facility_capacities = facilities_df.set_index('FacilityID')['MaxCapacity']

    # Get the intersection of indexes
    common_facilities = production_by_facility.index.intersection(facility_capacities.index)

    logger.info(f"Number of facilities in production data: {len(production_by_facility)}")
    logger.info(f"Number of facilities in capacity data: {len(facility_capacities)}")
    logger.info(f"Number of common facilities: {len(common_facilities)}")

    if len(common_facilities) == 0:
        logger.error("No common facilities found between production and capacity data")
        validation_results.append(("Production Capacity", False))
    else:
        capacity_check = production_by_facility.loc[common_facilities] <= facility_capacities.loc[common_facilities]
        validation_results.append(("Production Capacity", capacity_check.all()))

        # Log detailed capacity information
        for facility in common_facilities:
            prod = production_by_facility.loc[facility]
            cap = facility_capacities.loc[facility]
            logger.info(f"Facility {facility}: Production = {prod}, Capacity = {cap}")
            if prod > cap:
                logger.warning(f"Capacity violated for Facility {facility}")

    # Check raw material balance
    logger.info("Products DataFrame details:")
    logger.info(f"Columns: {products_df.columns}")
    logger.info(f"Index: {products_df.index}")
    logger.info(f"Data types:\n{products_df.dtypes}")
    logger.info(f"First few rows:\n{products_df.head().to_string()}")

    if 'IsRawMaterial' in products_df.columns:
        raw_materials = products_df[products_df['IsRawMaterial']]['ProductID'].tolist()
    else:
        logger.warning("'IsRawMaterial' column not found in products_df. Assuming all products except the first are raw materials.")
        if 'ProductID' in products_df.columns:
            raw_materials = products_df['ProductID'].tolist()[1:]  # Assume first product is finished product
        else:
            logger.error("'ProductID' column not found in products_df. Cannot determine raw materials.")
            raw_materials = []

    logger.info(f"Raw materials: {raw_materials}")

    for facility in facilities_df['FacilityID']:
        for raw_material in raw_materials:
            sourced = sourcing[(sourcing['FacilityID'] == facility) & (sourcing['ProductID'] == raw_material)]['Value'].sum()
            used = production[production['FacilityID'] == facility]['Value'].sum() * \
                   products_df.loc[products_df['ProductID'] == raw_material, 'ConversionFactor'].values[0]
            balance_check = np.isclose(sourced, used, rtol=1e-5)
            validation_results.append((f"Raw Material Balance (Facility {facility}, Product {raw_material})", balance_check))
            if not balance_check:
                logger.warning(f"Raw material balance mismatch: Facility {facility}, Product {raw_material}")
                logger.warning(f"Sourced: {sourced}, Used: {used}")

    # Check demand satisfaction
    distribution_by_post_office = distribution.groupby('PostOfficeID')['Value'].sum()
    post_office_demands = post_offices_df.set_index('PostOfficeID')['DoloDemandMin']

    # Get the intersection of indexes
    common_post_offices = distribution_by_post_office.index.intersection(post_office_demands.index)

    logger.info(f"Number of post offices in distribution data: {len(distribution_by_post_office)}")
    logger.info(f"Number of post offices in demand data: {len(post_office_demands)}")
    logger.info(f"Number of common post offices: {len(common_post_offices)}")

    if len(common_post_offices) == 0:
        logger.error("No common post offices found between distribution and demand data")
        validation_results.append(("Demand Satisfaction", False))
    else:
        demand_check = distribution_by_post_office.loc[common_post_offices] >= post_office_demands.loc[common_post_offices]
        validation_results.append(("Demand Satisfaction", demand_check.all()))

        # Log detailed demand information
        unmet_demand = post_office_demands.loc[common_post_offices][~demand_check]
        if not unmet_demand.empty:
            logger.warning("Post offices with unmet demand:")
            for po, demand in unmet_demand.items():
                dist = distribution_by_post_office.loc[po]
                logger.warning(f"Post Office {po}: Demand = {demand}, Distribution = {dist}")

    # Check production-distribution balance
    total_production = production['Value'].sum()
    total_distribution = distribution['Value'].sum()
    balance_check = np.isclose(total_production, total_distribution, rtol=1e-5)
    validation_results.append(("Production-Distribution Balance", balance_check))
    if not balance_check:
        logger.warning(f"Production-Distribution mismatch: Production = {total_production}, Distribution = {total_distribution}")

    return validation_results

if __name__ == "__main__":
    logger = setup_logging()

    try:
        model = optimize_supply_chain()
        logger.info("Model built successfully. Ready for solving.")
        
        solve_model(model, 'CBC')

        # Extract solution
        production, sourcing, distribution = extract_solution(model)
        

        # Print some statistics
        logger.info(f"Total Production: {production['Value'].sum()}")
        logger.info(f"Total Sourcing: {sourcing['Value'].sum()}")
        logger.info(f"Total Distribution: {distribution['Value'].sum()}")

        # Push solution to database
        push_solution_to_db(production, sourcing, distribution)
        logger.info("Solution pushed to database successfully.")
        
        # Fetch and verify the solution from the database
        db_production, db_sourcing, db_distribution = fetch_solution_from_db()
        if db_production is not None:
            logger.info(f"Fetched from DB - Production records: {len(db_production)}")
            logger.info(f"Fetched from DB - Sourcing records: {len(db_sourcing)}")
            logger.info(f"Fetched from DB - Distribution records: {len(db_distribution)}")

        # Validate solution
        facilities_df = fetch_data("SELECT * FROM facility")
        products_df = fetch_data("SELECT * FROM product")
        suppliers_df = fetch_data("SELECT * FROM supplier")
        post_offices_df = fetch_data("SELECT * FROM post_office")

        # validation_results = validate_solution(production, sourcing, distribution, 
        #                                        facilities_df, products_df, suppliers_df, post_offices_df)

        # for check, result in validation_results:
        #     logger.info(f"{check}: {'Passed' if result else 'Failed'}")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        logger.error(traceback.format_exc())