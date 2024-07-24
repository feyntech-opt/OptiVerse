import pyomo.environ as pyo
import pandas as pd
from sqlalchemy import create_engine
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection
engine = create_engine('sqlite:///dolo_650_supply_chain.db', echo=False)

def fetch_data(query):
    return pd.read_sql(query, engine)

def optimize_supply_chain():
    start_time = time.time()
    logger.info("Starting supply chain optimization with Pyomo and CBC")

    # Fetch data from the database concurrently
    with ThreadPoolExecutor() as executor:
        future_to_df = {
            executor.submit(fetch_data, "SELECT * FROM facility"): "facilities_df",
            executor.submit(fetch_data, "SELECT * FROM product"): "products_df",
            executor.submit(fetch_data, "SELECT * FROM supplier"): "suppliers_df",
            executor.submit(fetch_data, "SELECT * FROM supplier_product"): "supplier_products_df",
            executor.submit(fetch_data, "SELECT * FROM post_office"): "post_offices_df",
            executor.submit(fetch_data, "SELECT * FROM transportation_link"): "transportation_links_df"
        }
        dataframes = {}
        for future in as_completed(future_to_df):
            df_name = future_to_df[future]
            dataframes[df_name] = future.result()

    # Unpack dataframes
    facilities_df = dataframes["facilities_df"]
    products_df = dataframes["products_df"]
    suppliers_df = dataframes["suppliers_df"]
    supplier_products_df = dataframes["supplier_products_df"]
    post_offices_df = dataframes["post_offices_df"]
    transportation_links_df = dataframes["transportation_links_df"]

    logger.info(f"Data fetching completed. Time taken: {time.time() - start_time:.2f} seconds")

    # Convert IsRawMaterial to boolean
    products_df['IsRawMaterial'] = products_df['IsRawMaterial'].astype(bool)

    # Create Pyomo model
    model = pyo.ConcreteModel()

    # Define sets
    model.facilities = pyo.Set(initialize=facilities_df.FacilityID.tolist())
    model.products = pyo.Set(initialize=products_df.ProductID.tolist())
    model.suppliers = pyo.Set(initialize=suppliers_df.SupplierID.tolist())
    model.post_offices = pyo.Set(initialize=post_offices_df.PostOfficeID.tolist())
    model.raw_materials = pyo.Set(initialize=products_df[products_df.IsRawMaterial].ProductID.tolist())
    model.finished_products = pyo.Set(initialize=products_df[~products_df.IsRawMaterial].ProductID.tolist())

    # Define variables
    model.production = pyo.Var(model.facilities, model.finished_products, domain=pyo.NonNegativeReals)
    model.sourcing = pyo.Var(model.suppliers, model.raw_materials, model.facilities, domain=pyo.NonNegativeReals)
    model.distribution = pyo.Var(model.facilities, model.post_offices, domain=pyo.NonNegativeReals)

    # Objective function
    def obj_rule(model):
        return (
            sum(model.distribution[f, po] * products_df[products_df.Name == 'Dolo 650'].PricePerUnit.values[0]
                for f in model.facilities for po in model.post_offices) -
            sum(model.sourcing[s, p, f] * supplier_products_df[(supplier_products_df.SupplierID == s) & 
                                                               (supplier_products_df.ProductID == p)].Cost.values[0]
                for s in model.suppliers 
                for p in model.raw_materials 
                for f in model.facilities) -
            sum(model.production[f, p] * facilities_df[facilities_df.FacilityID == f].ManufacturingCostMax.values[0]
                for f in model.facilities 
                for p in model.finished_products) -
            sum(model.distribution[f, po] * transportation_links_df[(transportation_links_df.FromFacilityID == f) & 
                                                                    (transportation_links_df.ToPostOfficeID == po)].TotalCost.values[0]
                for f in model.facilities for po in model.post_offices)
        )
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Constraints
    def production_capacity_rule(model, f):
        return sum(model.production[f, p] for p in model.finished_products) <= facilities_df[facilities_df.FacilityID == f].MaxCapacity.values[0]
    model.production_capacity = pyo.Constraint(model.facilities, rule=production_capacity_rule)

    def raw_material_balance_rule(model, f, p):
        if p in model.raw_materials:
            return sum(model.sourcing[s, p, f] for s in model.suppliers) == \
                   sum(model.production[f, fp] * products_df[products_df.ProductID == p].ConversionFactor.values[0]
                       for fp in model.finished_products)
        else:
            return pyo.Constraint.Skip
    model.raw_material_balance = pyo.Constraint(model.facilities, model.products, rule=raw_material_balance_rule)

    def demand_satisfaction_rule(model, po):
        return sum(model.distribution[f, po] for f in model.facilities) >= post_offices_df[post_offices_df.PostOfficeID == po].DoloDemandMin.values[0]
    model.demand_satisfaction = pyo.Constraint(model.post_offices, rule=demand_satisfaction_rule)

    def production_distribution_balance_rule(model):
        return sum(model.production[f, p] for f in model.facilities for p in model.finished_products) == \
               sum(model.distribution[f, po] for f in model.facilities for po in model.post_offices)
    model.production_distribution_balance = pyo.Constraint(rule=production_distribution_balance_rule)

    logger.info("Model created. Starting optimization...")

    # Solve the model
    solver = pyo.SolverFactory('cbc')
    solver.options['seconds'] = 300  # Set time limit to 5 minutes
    results = solver.solve(model, tee=True)

    logger.info(f"Optimization completed. Time taken: {time.time() - start_time:.2f} seconds")
    logger.info(f"Solver Status: {results.solver.status}")
    logger.info(f"Termination Condition: {results.solver.termination_condition}")
    logger.info(f"Objective Value: {pyo.value(model.obj)}")

    # Extract results
    optimization_results = {
        "status": str(results.solver.status),
        "termination_condition": str(results.solver.termination_condition),
        "objective_value": pyo.value(model.obj),
        "production": {(f, p): pyo.value(model.production[f, p]) 
                       for f in model.facilities 
                       for p in model.finished_products 
                       if pyo.value(model.production[f, p]) > 0},
        "sourcing": {(s, p, f): pyo.value(model.sourcing[s, p, f]) 
                     for s in model.suppliers 
                     for p in model.raw_materials 
                     for f in model.facilities 
                     if pyo.value(model.sourcing[s, p, f]) > 0},
        "distribution": {(f, po): pyo.value(model.distribution[f, po]) 
                         for f in model.facilities 
                         for po in model.post_offices 
                         if pyo.value(model.distribution[f, po]) > 0}
    }

    return optimization_results

if __name__ == "__main__":
    try:
        optimization_results = optimize_supply_chain()

        logger.info("Optimization Results:")
        logger.info(f"Status: {optimization_results['status']}")
        logger.info(f"Termination Condition: {optimization_results['termination_condition']}")
        logger.info(f"Objective Value: {optimization_results['objective_value']}")

        logger.info(f"Number of non-zero Production variables: {len(optimization_results['production'])}")
        logger.info(f"Number of non-zero Sourcing variables: {len(optimization_results['sourcing'])}")
        logger.info(f"Number of non-zero Distribution variables: {len(optimization_results['distribution'])}")

        logger.info("Sample Production Results:")
        for (facility_id, product_id), value in list(optimization_results['production'].items())[:5]:
            logger.info(f"Facility {facility_id}, Product {product_id}: {value}")

        logger.info("Sample Sourcing Results:")
        for (supplier_id, product_id, facility_id), value in list(optimization_results['sourcing'].items())[:5]:
            logger.info(f"Supplier {supplier_id}, Product {product_id}, Facility {facility_id}: {value}")

        logger.info("Sample Distribution Results:")
        for (facility_id, post_office_id), value in list(optimization_results['distribution'].items())[:5]:
            logger.info(f"From Facility {facility_id} to Post Office {post_office_id}: {value}")

    except Exception as e:
        logger.error(f"An error occurred during optimization: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())