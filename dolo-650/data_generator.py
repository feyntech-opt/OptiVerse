import pandas as pd
import numpy as np
import json
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import random
from tqdm import tqdm
from math import radians, sin, cos, sqrt, atan2
import logging

# Load the SQLAlchemy models (assuming they're in a file called 'models.py')
from models import Base, Facility, Product, Transaction, Supplier, Customer, Tax, Purchase, PostOffice, Transportation, TransportationLink

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load JSON parameters
with open('dolo-650/dolo_650_parameters.json', 'r') as f:
    params = json.load(f)

# Create SQLite database
engine = create_engine('sqlite:///dolo_650_supply_chain.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Load CSV data
df = pd.read_csv('dolo-650/final_India_pincode_list_with_cleaned_population.csv')

def random_date(start, end):
    return start + timedelta(
        seconds=random.randint(0, int((end - start).total_seconds()))
    )

def calculate_demand(population):
    min_demand = population * 1.07
    max_demand = population * 1.5
    target_demand = (min_demand + max_demand) / 2
    return min_demand, max_demand, target_demand

def clear_database():
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    for table_name in table_names:
        session.execute(text(f"DELETE FROM {table_name}"))
    session.commit()
    logger.info("All data cleared from the database.")

def generate_facility_data(total_demand_min, total_demand_max):
    facilities = []
    total_capacity = 0
    capacity_scale_factor = 1.0

    # First pass: create facilities with original capacities
    for facility in params['facilities']:
        if 'latitude' not in facility or 'longitude' not in facility:
            logger.warning(f"Facility {facility['name']} is missing latitude or longitude")
            continue
        facilities.append(Facility(
            Name=facility['name'],
            Type=facility['type'],
            City=facility['city'],
            State=facility['state'],
            Latitude=float(facility['latitude']),
            Longitude=float(facility['longitude']),
            MinCapacity=facility['min_capacity'],
            MaxCapacity=facility['max_capacity'],
            StorageCostMin=facility['storage_cost_min'],
            StorageCostMax=facility['storage_cost_max'],
            ManufacturingCostMin=facility['manufacturing_cost_min'],
            ManufacturingCostMax=facility['manufacturing_cost_max']
        ))
        total_capacity += facility['max_capacity']

    # Check if total capacity is less than total demand, and adjust if necessary
    if total_capacity < total_demand_max:
        capacity_scale_factor = total_demand_max / total_capacity * 1.1  # Add 10% buffer
        logger.info(f"Adjusting facility capacities. Scale factor: {capacity_scale_factor}")
        
        for facility in facilities:
            facility.MinCapacity = int(facility.MinCapacity * capacity_scale_factor)
            facility.MaxCapacity = int(facility.MaxCapacity * capacity_scale_factor)
        
        total_capacity = sum(facility.MaxCapacity for facility in facilities)

    session.add_all(facilities)
    session.commit()
    
    logger.info(f"Generated {len(facilities)} facilities")
    logger.info(f"Total facility capacity: {total_capacity}")
    logger.info(f"Total demand range: {total_demand_min} - {total_demand_max}")

    return total_capacity

def generate_product_data():
    products = [
        Product(
            Name="Dolo 650",
            Unit="Tablet",
            IsRawMaterial=False,
            ConversionFactor=1.0,  # 1 tablet
            PricePerUnit=params['product']['price_per_unit']
        ),
        Product(
            Name="Para-Aminophenol (PAP)",
            Unit="kg",
            IsRawMaterial=True,
            ConversionFactor=0.00048,  # 0.48g per tablet (65% of 0.75g, scaled to kg)
            PricePerUnit=(params['raw_materials'][0]['unit_cost_min'] + params['raw_materials'][0]['unit_cost_max']) / 2
        ),
        Product(
            Name="Acetic Anhydride",
            Unit="kg",
            IsRawMaterial=True,
            ConversionFactor=0.000375,  # 0.375g per tablet (50% of 0.75g, scaled to kg)
            PricePerUnit=(params['raw_materials'][1]['unit_cost_min'] + params['raw_materials'][1]['unit_cost_max']) / 2
        ),
        Product(
            Name="Catalysts",
            Unit="kg",
            IsRawMaterial=True,
            ConversionFactor=0.0000075,  # 0.0075g per tablet (1% of 0.75g, scaled to kg)
            PricePerUnit=(params['raw_materials'][2]['unit_cost_min'] + params['raw_materials'][2]['unit_cost_max']) / 2
        ),
        Product(
            Name="Solvents",
            Unit="L",
            IsRawMaterial=True,
            ConversionFactor=0.000075,  # 0.075mL per tablet (10% of 0.75g, assumed density of 1g/mL)
            PricePerUnit=(params['raw_materials'][3]['unit_cost_min'] + params['raw_materials'][3]['unit_cost_max']) / 2
        )
    ]
    
    session.add_all(products)
    session.commit()
    logger.info(f"Generated data for {len(products)} products (1 finished product and {len(products)-1} raw materials)")

    # Log details of each product
    for product in products:
        logger.info(f"Product: {product.Name}")
        logger.info(f"  Unit: {product.Unit}")
        logger.info(f"  Is Raw Material: {product.IsRawMaterial}")
        logger.info(f"  Conversion Factor: {product.ConversionFactor}")
        logger.info(f"  Price Per Unit: {product.PricePerUnit}")
        logger.info("---")

def generate_supplier_data():
    suppliers = []
    sampled_locations = df.sample(n=len(params['suppliers']))
    for supplier, (_, location) in zip(params['suppliers'], sampled_locations.iterrows()):
        suppliers.append(Supplier(
            Name=supplier['name'],
            City=location['OfficeName'],
            State=location['StateName'],
            Latitude=location['Latitude'],
            Longitude=location['Longitude'],
            ContactDetails=f"contact@{supplier['name'].lower().replace(' ', '')}.com"
        ))
    session.add_all(suppliers)
    session.commit()
    logger.info(f"Generated {len(suppliers)} suppliers")

def generate_customer_data():
    customers = []
    sampled_locations = df.sample(n=1000, replace=True)  # Generate 1000 customers
    for _, location in sampled_locations.iterrows():
        customers.append(Customer(
            Name=f"Customer_{random.randint(1, 1000000)}",
            CustomerType=random.choice(params['customer_types']),
            City=location['OfficeName'],
            State=location['StateName'],
            Latitude=location['Latitude'],
            Longitude=location['Longitude'],
            ContactDetails=f"customer_{random.randint(1, 1000000)}@example.com"
        ))
    session.add_all(customers)
    session.commit()
    logger.info("Generated 1000 customers")

def generate_tax_data():
    tax = Tax(TaxType="GST", TaxRate=params['tax']['gst_rate'])
    session.add(tax)
    session.commit()
    logger.info("Generated tax data")

def generate_transportation_data():
    transportations = []
    for transport in params['transportation_types']:
        transportations.append(Transportation(
            Type=transport['type'],
            CostPerKm=transport['cost_per_km'],
            Description=transport['description']
        ))
    session.add_all(transportations)
    session.commit()
    logger.info(f"Generated {len(transportations)} transportation types")

def generate_post_office_data():
    post_offices = []
    total_demand_min = 0
    total_demand_max = 0
    
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Generating Post Office data"):
        population = row['Population']
        min_demand, max_demand, target_demand = calculate_demand(population)
        
        total_demand_min += min_demand
        total_demand_max += max_demand
        
        post_office = PostOffice(
            OfficeName=row['OfficeName'],
            Pincode=row['Pincode'],
            OfficeType=row['OfficeType'],
            DeliveryStatus=row['Delivery'],
            DivisionName=row['DivisionName'],
            RegionName=row['RegionName'],
            CircleName=row['CircleName'],
            Taluk=row['District'],
            DistrictName=row['District'],
            StateName=row['StateName'],
            Latitude=row['Latitude'],
            Longitude=row['Longitude'],
            PopulationPerPO=population,
            DoloDemandMin=min_demand,
            DoloDemandMax=max_demand,
            DoloDemandTarget=target_demand
        )
        
        # Add demand for each customer type
        for customer_type, share in params['demand_distribution'].items():
            setattr(post_office, f"{customer_type}DemandMin", min_demand * share)
            setattr(post_office, f"{customer_type}DemandMax", max_demand * share)
            setattr(post_office, f"{customer_type}DemandTarget", target_demand * share)
        
        post_offices.append(post_office)
    
    session.bulk_save_objects(post_offices)
    session.commit()
    logger.info(f"Generated {len(post_offices)} post office data points")
    return total_demand_min, total_demand_max

def generate_transaction_and_purchase_data():
    facilities = session.query(Facility).all()
    suppliers = session.query(Supplier).all()
    customers = session.query(Customer).all()
    product = session.query(Product).first()
    tax = session.query(Tax).first()

    transactions = []
    purchases = []
    
    for _ in tqdm(range(10000), desc="Generating Transactions and Purchases"):
        transaction_type = random.choice(["Sourcing", "Distribution"])
        if transaction_type == "Sourcing":
            facility = random.choice(facilities)
            supplier = random.choice(suppliers)
            customer = None
        else:
            facility = random.choice([f for f in facilities if f.Type == "Manufacturing"])
            supplier = None
            customer = random.choice(customers)

        quantity = random.randint(1000, 10000)
        price = quantity * product.PricePerUnit
        tax_amount = price * tax.TaxRate
        total_amount = price + tax_amount

        transaction = Transaction(
            Date=random_date(datetime(2023, 1, 1), datetime(2023, 12, 31)),
            Type=transaction_type,
            Quantity=quantity,
            Price=price,
            TaxAmount=tax_amount,
            TotalAmount=total_amount,
            FacilityID=facility.FacilityID,
            SupplierID=supplier.SupplierID if supplier else None,
            CustomerID=customer.CustomerID if customer else None
        )
        transactions.append(transaction)

        purchase = Purchase(
            TransactionID=transaction.TransactionID,
            ProductID=product.ProductID,
            Quantity=quantity,
            PricePerUnit=product.PricePerUnit,
            TaxID=tax.TaxID,
            TaxAmount=tax_amount,
            TotalAmount=total_amount
        )
        purchases.append(purchase)

    session.bulk_save_objects(transactions)
    session.bulk_save_objects(purchases)
    session.commit()
    logger.info(f"Generated {len(transactions)} transactions and {len(purchases)} purchases")

def haversine_distance(lat1, lon1, lat2, lon2):
    if any(not isinstance(x, (int, float)) for x in [lat1, lon1, lat2, lon2]):
        raise ValueError(f"Invalid coordinate types: {type(lat1)}, {type(lon1)}, {type(lat2)}, {type(lon2)}")
    
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance


def generate_transportation_link_data():
    facilities = session.query(Facility).all()
    post_offices = session.query(PostOffice).all()
    transportations = session.query(Transportation).all()

    transportation_links = []
    
    total_links = len(facilities) * len(post_offices) * len(transportations)
    
    with tqdm(total=total_links, desc="Generating Transportation Links") as pbar:
        for facility in facilities:
            if facility.Latitude is None or facility.Longitude is None:
                logger.warning(f"Facility {facility.Name} has invalid coordinates")
                pbar.update(len(post_offices) * len(transportations))
                continue

            for post_office in post_offices:
                if post_office.Latitude is None or post_office.Longitude is None:
                    logger.warning(f"Post Office {post_office.OfficeName} has invalid coordinates")
                    pbar.update(len(transportations))
                    continue

                try:
                    distance = haversine_distance(facility.Latitude, facility.Longitude, 
                                                  post_office.Latitude, post_office.Longitude)
                except ValueError as e:
                    logger.error(f"Error calculating distance: {e}")
                    logger.error(f"Facility: {facility.Name}, Coords: {facility.Latitude}, {facility.Longitude}")
                    logger.error(f"Post Office: {post_office.OfficeName}, Coords: {post_office.Latitude}, {post_office.Longitude}")
                    pbar.update(len(transportations))
                    continue

                for transportation in transportations:
                    total_cost = distance * transportation.CostPerKm

                    transportation_links.append(TransportationLink(
                        FromFacilityID=facility.FacilityID,
                        ToPostOfficeID=post_office.PostOfficeID,
                        TransportationID=transportation.TransportationID,
                        Distance=distance,
                        TotalCost=total_cost
                    ))
                    
                    pbar.update(1)

                if len(transportation_links) >= 100000:
                    session.bulk_save_objects(transportation_links)
                    session.commit()
                    transportation_links = []

    if transportation_links:
        session.bulk_save_objects(transportation_links)
        session.commit()
    
    logger.info(f"Generated transportation links for all facility-post office-transportation type combinations")


if __name__ == "__main__":
    try:
        # Uncomment the following line if you want to clear the database before generating new data
        # clear_database()
        
        generate_product_data()
        generate_supplier_data()
        generate_customer_data()
        generate_tax_data()
        generate_transportation_data()
        
        total_demand_min, total_demand_max = generate_post_office_data()
        logger.info(f"Total demand generated: {total_demand_min} - {total_demand_max}")
        
        total_capacity = generate_facility_data(total_demand_min, total_demand_max)
        logger.info(f"Total capacity generated: {total_capacity}")
        
        if total_capacity < total_demand_max:
            logger.warning(f"Total capacity ({total_capacity}) is less than maximum total demand ({total_demand_max})")
        else:
            logger.info(f"Total capacity ({total_capacity}) is sufficient to meet maximum total demand ({total_demand_max})")
        
        generate_transportation_link_data()
        generate_transaction_and_purchase_data()

        logger.info("Data generation complete.")
    except Exception as e:
        logger.error(f"An error occurred during data generation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        session.close()