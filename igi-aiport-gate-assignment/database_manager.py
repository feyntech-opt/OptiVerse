import json
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

Base = declarative_base()


# Association table for many-to-many relationship between gates and aircraft types
gate_aircraft_compatibility = Table('gate_aircraft_compatibility', Base.metadata,
    Column('gate_id', String, ForeignKey('gates.id')),
    Column('aircraft_type', String, ForeignKey('aircraft_types.type'))
)

class Airport(Base):
    __tablename__ = 'airports'
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    iata_code = Column(String(3), nullable=False)
    icao_code = Column(String(4), nullable=False)
    timezone = Column(String, nullable=False)

class Terminal(Base):
    __tablename__ = 'terminals'
    id = Column(String, primary_key=True)
    airport_id = Column(String, ForeignKey('airports.id'))
    name = Column(String, nullable=False)
    capacity = Column(Integer)

class Gate(Base):
    __tablename__ = 'gates'
    id = Column(String, primary_key=True)
    terminal_id = Column(String, ForeignKey('terminals.id'))
    number = Column(String, nullable=False)
    is_boarding_bridge = Column(Boolean, default=True)
    max_passengers = Column(Integer)
    compatible_aircraft_types = relationship('AircraftType', secondary=gate_aircraft_compatibility, back_populates='compatible_gates')
    
class AircraftType(Base):
    __tablename__ = 'aircraft_types'
    type = Column(String, primary_key=True)
    wingspan = Column(Float)
    length = Column(Float)
    height = Column(Float)
    max_passengers = Column(Integer)
    compatible_gates = relationship('Gate', secondary=gate_aircraft_compatibility, back_populates='compatible_aircraft_types')

class Aircraft(Base):
    __tablename__ = 'aircraft'
    registration = Column(String, primary_key=True)
    type = Column(String, ForeignKey('aircraft_types.type'))
    airline = Column(String, ForeignKey('airlines.iata_code'))
    next_maintenance_due = Column(DateTime)
    
    aircraft_type = relationship("AircraftType")

class Airline(Base):
    __tablename__ = 'airlines'
    iata_code = Column(String(2), primary_key=True)
    name = Column(String, nullable=False)
    is_domestic = Column(Boolean)

class Flight(Base):
    __tablename__ = 'flights'
    id = Column(String, primary_key=True)
    airline = Column(String, ForeignKey('airlines.iata_code'))
    aircraft_registration = Column(String, ForeignKey('aircraft.registration'))
    origin = Column(String, ForeignKey('airports.id'))
    destination = Column(String, ForeignKey('airports.id'))
    scheduled_departure = Column(DateTime)
    scheduled_arrival = Column(DateTime)
    actual_departure = Column(DateTime)
    actual_arrival = Column(DateTime)
    passenger_count = Column(Integer)
    connecting_flight_id = Column(String, ForeignKey('flights.id'))

class GroundService(Base):
    __tablename__ = 'ground_services'
    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)
    provider = Column(String)
    average_duration_minutes = Column(Integer)

class WeatherCondition(Base):
    __tablename__ = 'weather_conditions'
    id = Column(Integer, primary_key=True)
    airport_id = Column(String, ForeignKey('airports.id'))
    timestamp = Column(DateTime)
    temperature = Column(Float)
    wind_speed = Column(Float)
    visibility = Column(Float)
    condition = Column(String)

class AirportLocation(Base):
    __tablename__ = 'airport_locations'
    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)  # 'GATE', 'HANGAR', 'REMOTE_STAND'
    location_x = Column(Float)
    location_y = Column(Float)
    
    
class TransitTime(Base):
    __tablename__ = 'transit_times'
    id = Column(Integer, primary_key=True)
    from_location = Column(String, ForeignKey('airport_locations.id'))
    to_location = Column(String, ForeignKey('airport_locations.id'))
    transport_type = Column(String)  # 'PASSENGER', 'SHUTTLE', 'AIRCRAFT'
    time_minutes = Column(Float)

def create_database():
    engine = create_engine('sqlite:///igi_airport.db', echo=True)
    Base.metadata.create_all(engine)
    return engine

def get_or_create(session, model, **kwargs):
    try:
        instance = session.query(model).filter_by(**kwargs).one()
        return instance, False
    except NoResultFound:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance, True
    
def generate_sample_data(session, params):
    # Airport
    airport, _ = get_or_create(session, Airport, **params['airport_details'])

    # Terminals
    for terminal_data in params['terminal_details']:
        get_or_create(session, Terminal, airport_id=airport.id, **terminal_data)

    # Gates and Airport Locations
    for terminal_data in params['terminal_details']:
        for i in range(1, params['gates_per_terminal'] + 1):
            gate_id = f"{terminal_data['id']}-{i}"
            location_x = random.uniform(0, 1000)
            location_y = random.uniform(0, 1000)
            gate, _ = get_or_create(session, Gate,
                id=gate_id,
                terminal_id=terminal_data['id'],
                number=str(i),
                is_boarding_bridge=random.choice(params['gate_types']['boarding_bridge']),
                max_passengers=random.choice(params['gate_types']['max_passengers'])
            )
            get_or_create(session, AirportLocation,
                id=gate_id,
                type='GATE',
                location_x=location_x,
                location_y=location_y
            )

    # Hangars and Remote Stands
    number_of_hangars = params.get('number_of_hangars', 5)  # Default to 5 if not specified
    number_of_remote_stands = params.get('number_of_remote_stands', 10)  # Default to 10 if not specified

    for i in range(number_of_hangars):
        get_or_create(session, AirportLocation,
            id=f"HANGAR-{i+1}",
            type='HANGAR',
            location_x=random.uniform(0, 1000),
            location_y=random.uniform(0, 1000)
        )
    for i in range(number_of_remote_stands):
        get_or_create(session, AirportLocation,
            id=f"REMOTE-{i+1}",
            type='REMOTE_STAND',
            location_x=random.uniform(0, 1000),
            location_y=random.uniform(0, 1000)
        )

    # Aircraft Types
    aircraft_types = []
    for aircraft_type_data in params['aircraft_types']:
        aircraft_type, _ = get_or_create(session, AircraftType, **aircraft_type_data)
        aircraft_types.append(aircraft_type)

    # Assign compatible aircraft types to gates
    gates = session.query(Gate).all()
    for gate in gates:
        gate.compatible_aircraft_types = random.sample(aircraft_types, k=random.randint(2, 4))

    # Airlines
    airlines = []
    for airline_data in params['airlines']:
        airline, _ = get_or_create(session, Airline, **airline_data)
        airlines.append(airline)

    # Aircraft
    for _ in range(params['number_of_aircraft']):
        get_or_create(session, Aircraft,
            registration=f"VT-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))}",
            type=random.choice(aircraft_types).type,
            airline=random.choice(airlines).iata_code,
            next_maintenance_due=datetime.now() + timedelta(days=random.randint(1, 365))
        )

    # Flights for a single day
    existing_flights = set(flight.id for flight in session.query(Flight).all())
    new_flights = []
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for _ in range(params['number_of_flights']):
        airline = random.choice(airlines)
        aircraft = random.choice(session.query(Aircraft).all())
        
        # Fetch the AircraftType object
        aircraft_type = session.query(AircraftType).filter_by(type=aircraft.type).first()
        if not aircraft_type:
            print(f"Warning: AircraftType not found for {aircraft.type}. Using default max passengers.")
            max_passengers = 200  # Default value
        else:
            max_passengers = aircraft_type.max_passengers

        is_domestic = airline.is_domestic
        origin = 'DEL' if random.random() < 0.5 else random.choice(params['domestic_airports'] if is_domestic else params['international_airports'])
        destination = random.choice(params['domestic_airports'] if is_domestic else params['international_airports']) if origin == 'DEL' else 'DEL'
        
        # Generate departure time within the single day
        scheduled_departure = start_date + timedelta(minutes=random.randint(0, 24*60-1))
        flight_duration = timedelta(minutes=random.randint(60, 600))  # 1 to 10 hours
        scheduled_arrival = scheduled_departure + flight_duration
        
        delay = timedelta(minutes=random.randint(-30, 120))
        actual_departure = scheduled_departure + delay
        actual_arrival = scheduled_arrival + delay

        while True:
            flight_id = f"{airline.iata_code}{random.randint(1000, 9999)}"
            if flight_id not in existing_flights:
                existing_flights.add(flight_id)
                break

        new_flights.append(Flight(
            id=flight_id,
            airline=airline.iata_code,
            aircraft_registration=aircraft.registration,
            origin=origin,
            destination=destination,
            scheduled_departure=scheduled_departure,
            scheduled_arrival=scheduled_arrival,
            actual_departure=actual_departure,
            actual_arrival=actual_arrival,
            passenger_count=random.randint(50, max_passengers)
        ))
    session.add_all(new_flights)

    # Ground Services
    for service_data in params['ground_services']:
        get_or_create(session, GroundService, **service_data)

    # Weather Conditions for a single day
    new_weather_conditions = []
    for hour in range(24):
        new_weather_conditions.append(WeatherCondition(
            airport_id='DEL',
            timestamp=start_date + timedelta(hours=hour),
            temperature=random.uniform(15, 40),
            wind_speed=random.uniform(0, 30),
            visibility=random.uniform(1, 10),
            condition=random.choice(['Clear', 'Partly Cloudy', 'Cloudy', 'Rain', 'Fog'])
        ))
    session.add_all(new_weather_conditions)
    
    # Generate Transit Times
    generate_transit_times(session)

    try:
        session.commit()
        print("Sample data generated successfully.")
    except IntegrityError as e:
        session.rollback()
        print(f"Error generating sample data: {e}")
        
def generate_transit_times(session):
    locations = session.query(AirportLocation).all()
    
    # Actual distances and speeds (in km and km/h)
    distances = {
        ('T1', 'T2'): 1.5, ('T1', 'T3'): 2.0, ('T2', 'T3'): 1.8,
        ('T1', 'RW10-28'): 2.0, ('T2', 'RW10-28'): 2.5, ('T3', 'RW10-28'): 2.2,
        ('T1', 'RW11-29'): 2.2, ('T2', 'RW11-29'): 2.3, ('T3', 'RW11-29'): 2.0,
        ('T1', 'RW09-27'): 1.8, ('T2', 'RW09-27'): 2.1, ('T3', 'RW09-27'): 1.9
    }
    speeds = {
        'PASSENGER': 5,  # 5 km/h walking speed
        'SHUTTLE': 20,   # 20 km/h shuttle speed
        'AIRCRAFT': 25   # 25 km/h aircraft taxiing speed
    }

    for from_loc in locations:
        for to_loc in locations:
            if from_loc.id != to_loc.id:
                for transport_type in ['PASSENGER', 'SHUTTLE', 'AIRCRAFT']:
                    # Determine the distance
                    if (from_loc.id, to_loc.id) in distances:
                        distance = distances[(from_loc.id, to_loc.id)]
                    elif (to_loc.id, from_loc.id) in distances:
                        distance = distances[(to_loc.id, from_loc.id)]
                    else:
                        # If not a predefined distance, calculate based on coordinates
                        distance = ((from_loc.location_x - to_loc.location_x)**2 + 
                                    (from_loc.location_y - to_loc.location_y)**2)**0.5 / 100  # Assume 100 units = 1 km

                    # Calculate time in minutes
                    time_minutes = (distance / speeds[transport_type]) * 60

                    # Create TransitTime record
                    transit_time, created = get_or_create(session, TransitTime,
                        from_location=from_loc.id,
                        to_location=to_loc.id,
                        transport_type=transport_type,
                        time_minutes=time_minutes
                    )
                    if created:
                        print(f"Created transit time: {from_loc.id} to {to_loc.id} via {transport_type}: {time_minutes:.2f} minutes")
                        
def drop_all_tables(engine):
    Base.metadata.drop_all(engine)
    print("All tables dropped.")

def main():
    try:
        # Load JSON parameters
        with open('igi-aiport-gate-assignment/igi-airport-params-json.json', 'r') as f:
            params = json.load(f)

        engine = create_engine('sqlite:///igi_airport.db', echo=True)
        
        # Drop all existing tables
        drop_all_tables(engine)
        
        # Create new tables
        Base.metadata.create_all(engine)
        
        Session = sessionmaker(bind=engine)
        session = Session()

        generate_sample_data(session, params)

        session.close()
        print("Sample data generated successfully.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()