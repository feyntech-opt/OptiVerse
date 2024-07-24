import traceback
import pyomo.environ as pyo
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

engine = create_engine('sqlite:///dolo_650_supply_chain.db', echo=False)

def fetch_data(query):
    return pd.read_sql(query, engine)

def optimize_supply_chain():
    start_time = time.time()
    logger.info("Starting fast-build supply chain model construction")

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

    # Create Pyomo model
    model = pyo.ConcreteModel()

    # Define sets
    model.facilities = pyo.Set(initialize=facilities)
    model.products = pyo.Set(initialize=products)
    model.suppliers = pyo.Set(initialize=suppliers)
    model.post_offices = pyo.Set(initialize=post_offices)
    model.raw_materials = pyo.Set(initialize=raw_materials)
    model.finished_products = pyo.Set(initialize=finished_products)

    # Define variables
    model.production = pyo.Var(model.facilities, model.finished_products, domain=pyo.NonNegativeReals)
    model.sourcing = pyo.Var(model.suppliers, model.raw_materials, model.facilities, domain=pyo.NonNegativeReals)
    model.distribution = pyo.Var(model.facilities, model.post_offices, domain=pyo.NonNegativeReals)

    logger.info(f"Sets and variables defined. Time taken: {time.time() - start_time:.2f} seconds")

    # Objective function
    def obj_rule(model):
        return (
            sum(model.distribution[f, po] * product_prices[finished_products[0]]
                for f in model.facilities for po in model.post_offices) -
            sum(model.sourcing[s, p, f] * supplier_product_costs.get((s, p), 0)
                for s in model.suppliers 
                for p in model.raw_materials 
                for f in model.facilities) -
            sum(model.production[f, p] * manufacturing_costs[f]
                for f in model.facilities 
                for p in model.finished_products) -
            sum(model.distribution[f, po] * transport_links.get((f, po), 0)
                for f in model.facilities for po in model.post_offices)
        )
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    logger.info(f"Objective function defined. Time taken: {time.time() - start_time:.2f} seconds")

    # Constraints
    model.production_capacity = pyo.ConstraintList()
    for f in model.facilities:
        model.production_capacity.add(
            sum(model.production[f, p] for p in model.finished_products) <= facility_capacities[f]
        )

    model.raw_material_balance = pyo.ConstraintList()
    for f in model.facilities:
        for p in model.raw_materials:
            model.raw_material_balance.add(
                sum(model.sourcing[s, p, f] for s in model.suppliers) == 
                sum(model.production[f, fp] * conversion_factors[p] for fp in model.finished_products)
            )

    model.demand_satisfaction = pyo.ConstraintList()
    for po in model.post_offices:
        model.demand_satisfaction.add(
            sum(model.distribution[f, po] for f in model.facilities) >= post_office_demands[po]
        )

    model.production_distribution_balance = pyo.Constraint(
        expr=sum(model.production[f, p] for f in model.facilities for p in model.finished_products) == 
             sum(model.distribution[f, po] for f in model.facilities for po in model.post_offices)
    )

    logger.info(f"Constraints defined. Time taken: {time.time() - start_time:.2f} seconds")
    logger.info(f"Model building completed. Total time taken: {time.time() - start_time:.2f} seconds")

    return model

def solve_with_logging(model, solver_name):
    solver = pyo.SolverFactory(solver_name)
    
    logger.info(f"Solving with {solver_name}")
    results = solver.solve(model, tee=True)
    
    logger.info(f"{solver_name} Solver Status: {results.solver.status}")
    logger.info(f"{solver_name} Termination Condition: {results.solver.termination_condition}")
    
    if results.solver.termination_condition == pyo.TerminationCondition.optimal:
        # Load the solution
        logger.info("Attempting to load solution...")
        model.solutions.load_from(results)
        
        # Debug: Check if variables have values
        logger.info("Checking variable values...")
        for v in model.component_data_objects(pyo.Var):
            if v.value is None:
                logger.warning(f"Variable {v.name} has no value")
            else:
                logger.debug(f"Variable {v.name} = {v.value}")
        
        # Now try to access variable values
        try:
            objective_value = pyo.value(model.obj)
            logger.info(f"{solver_name} Objective Value: {objective_value}")

            # Print some sample variable values
            logger.info("Sample Production Values:")
            for f in list(model.facilities)[:2]:
                for p in list(model.finished_products)[:2]:
                    logger.info(f"Production[{f},{p}] = {pyo.value(model.production[f,p])}")

            logger.info("Sample Distribution Values:")
            for f in list(model.facilities)[:2]:
                for po in list(model.post_offices)[:2]:
                    logger.info(f"Distribution[{f},{po}] = {pyo.value(model.distribution[f,po])}")

        except ValueError as e:
            logger.error(f"Error accessing variable values with {solver_name}: {str(e)}")
    else:
        logger.warning(f"{solver_name} terminated with condition: {results.solver.termination_condition}")
    
    return results

if __name__ == "__main__":
    try:
        model = optimize_supply_chain()
        logger.info("Model built successfully. Ready for solving.")
        
        solvers_to_try = ['cbc'] #, 'ipopt', 'gurobi', 'cplex', 'glpk', ]

        for solver_name in solvers_to_try:
            try:
                results = solve_with_logging(model, solver_name)
            except Exception as e:
                logger.error(f"Error with {solver_name}: {str(e)}")
                logger.error(traceback.format_exc())

    except Exception as e:
        logger.error(f"An error occurred during model building: {str(e)}")
        logger.error(traceback.format_exc())