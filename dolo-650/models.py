from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Facility(Base):
    __tablename__ = 'facility'
    FacilityID = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(String)
    Type = Column(String)
    City = Column(String)
    State = Column(String)
    Latitude = Column(Float)
    Longitude = Column(Float)
    MinCapacity = Column(Integer)
    MaxCapacity = Column(Integer)
    StorageCostMin = Column(Float)
    StorageCostMax = Column(Float)
    ManufacturingCostMin = Column(Float)
    ManufacturingCostMax = Column(Float)

class Product(Base):
    __tablename__ = 'product'
    ProductID = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(String)
    Unit = Column(String)
    IsRawMaterial = Column(Boolean)
    ConversionFactor = Column(Float)  # Amount needed for 1 Dolo 650 tablet
    PricePerUnit = Column(Float)

class Supplier(Base):
    __tablename__ = 'supplier'
    SupplierID = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(String)
    City = Column(String)
    State = Column(String)
    Latitude = Column(Float)
    Longitude = Column(Float)
    ContactDetails = Column(String)
    products = relationship("SupplierProduct", back_populates="supplier")

class SupplierProduct(Base):
    __tablename__ = 'supplier_product'
    SupplierProductID = Column(Integer, primary_key=True, autoincrement=True)
    SupplierID = Column(Integer, ForeignKey('supplier.SupplierID'))
    ProductID = Column(Integer, ForeignKey('product.ProductID'))
    Cost = Column(Float)
    supplier = relationship("Supplier", back_populates="products")
    product = relationship("Product", back_populates="suppliers")

class Customer(Base):
    __tablename__ = 'customer'
    CustomerID = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(String)
    CustomerType = Column(String)
    City = Column(String)
    State = Column(String)
    Latitude = Column(Float)
    Longitude = Column(Float)
    ContactDetails = Column(String)

class Tax(Base):
    __tablename__ = 'tax'
    TaxID = Column(Integer, primary_key=True, autoincrement=True)
    TaxType = Column(String)
    TaxRate = Column(Float)

class Transaction(Base):
    __tablename__ = 'transaction'
    TransactionID = Column(Integer, primary_key=True, autoincrement=True)
    Date = Column(String)
    Type = Column(String)
    Quantity = Column(Integer)
    Price = Column(Float)
    TaxAmount = Column(Float)
    TotalAmount = Column(Float)
    FacilityID = Column(Integer, ForeignKey('facility.FacilityID'))
    SupplierID = Column(Integer, ForeignKey('supplier.SupplierID'))
    CustomerID = Column(Integer, ForeignKey('customer.CustomerID'))

class Purchase(Base):
    __tablename__ = 'purchase'
    PurchaseID = Column(Integer, primary_key=True, autoincrement=True)
    TransactionID = Column(Integer, ForeignKey('transaction.TransactionID'))
    ProductID = Column(Integer, ForeignKey('product.ProductID'))
    Quantity = Column(Integer)
    PricePerUnit = Column(Float)
    TaxID = Column(Integer, ForeignKey('tax.TaxID'))
    TaxAmount = Column(Float)
    TotalAmount = Column(Float)

class PostOffice(Base):
    __tablename__ = 'post_office'
    PostOfficeID = Column(Integer, primary_key=True, autoincrement=True)
    OfficeName = Column(String)
    Pincode = Column(String)
    OfficeType = Column(String)
    DeliveryStatus = Column(String)
    DivisionName = Column(String)
    RegionName = Column(String)
    CircleName = Column(String)
    Taluk = Column(String)
    DistrictName = Column(String)
    StateName = Column(String)
    Latitude = Column(Float)
    Longitude = Column(Float)
    PopulationPerPO = Column(Float)
    DoloDemandMin = Column(Float)
    DoloDemandMax = Column(Float)
    DoloDemandTarget = Column(Float)
    RetailersDemandMin = Column(Float)
    RetailersDemandMax = Column(Float)
    RetailersDemandTarget = Column(Float)
    WholesalersDemandMin = Column(Float)
    WholesalersDemandMax = Column(Float)
    WholesalersDemandTarget = Column(Float)
    HospitalsDemandMin = Column(Float)
    HospitalsDemandMax = Column(Float)
    HospitalsDemandTarget = Column(Float)
    OnlinePharmaciesDemandMin = Column(Float)
    OnlinePharmaciesDemandMax = Column(Float)
    OnlinePharmaciesDemandTarget = Column(Float)
    GovernmentDemandMin = Column(Float)
    GovernmentDemandMax = Column(Float)
    GovernmentDemandTarget = Column(Float)

class Transportation(Base):
    __tablename__ = 'transportation'
    TransportationID = Column(Integer, primary_key=True, autoincrement=True)
    Type = Column(String)
    CostPerKm = Column(Float)
    Description = Column(String)

class TransportationLink(Base):
    __tablename__ = 'transportation_link'
    TransportationLinkID = Column(Integer, primary_key=True, autoincrement=True)
    FromFacilityID = Column(Integer, ForeignKey('facility.FacilityID'))
    ToPostOfficeID = Column(Integer, ForeignKey('post_office.PostOfficeID'))
    TransportationID = Column(Integer, ForeignKey('transportation.TransportationID'))
    Distance = Column(Float)
    TotalCost = Column(Float)
    
class ProductionSolution(Base):
    __tablename__ = 'production_solution'
    
    ProductionSolutionID = Column(Integer, primary_key=True, autoincrement=True)
    FacilityID = Column(Integer, ForeignKey('facility.FacilityID'))
    ProductID = Column(Integer, ForeignKey('product.ProductID'))
    Value = Column(Float)

class SourcingSolution(Base):
    __tablename__ = 'sourcing_solution'
    
    SourcingSolutionID = Column(Integer, primary_key=True, autoincrement=True)
    SupplierID = Column(Integer, ForeignKey('supplier.SupplierID'))
    ProductID = Column(Integer, ForeignKey('product.ProductID'))
    FacilityID = Column(Integer, ForeignKey('facility.FacilityID'))
    Value = Column(Float)

class DistributionSolution(Base):
    __tablename__ = 'distribution_solution'
    
    DistributionSolutionID = Column(Integer, primary_key=True, autoincrement=True)
    FacilityID = Column(Integer, ForeignKey('facility.FacilityID'))
    PostOfficeID = Column(Integer, ForeignKey('post_office.PostOfficeID'))
    Value = Column(Float)

Product.suppliers = relationship("SupplierProduct", back_populates="product")

# Create SQLite database
engine = create_engine('sqlite:///dolo_650_supply_chain.db')
Base.metadata.create_all(engine)