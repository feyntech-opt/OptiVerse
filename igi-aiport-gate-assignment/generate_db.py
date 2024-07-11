import sqlite3
import random
from datetime import datetime, timedelta
import json

import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# Import the IGI_PARAMS and generation functions from the previous script
import generate_data as datagen

def create_database():
    conn = sqlite3.connect('igi_airport_data.db')
    c = conn.cursor()

    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS airport
                 (name TEXT, IATA_code TEXT, ICAO_code TEXT, time_zone TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS terminals
                 (terminal_id TEXT, description TEXT, capacity INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS gates
                 (gate_id TEXT, terminal_id TEXT, aircraft_compatibility TEXT, 
                  boarding_bridge INTEGER, remote_stand INTEGER, max_passengers INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS airlines
                 (airline_name TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS aircraft_types
                 (type TEXT, wingspan REAL, length REAL, height REAL, weight REAL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS flights
                 (flight_id TEXT, airline TEXT, aircraft_type TEXT, origin TEXT, destination TEXT,
                  flight_type TEXT, scheduled_departure_time TEXT, scheduled_arrival_time TEXT,
                  estimated_departure_time TEXT, estimated_arrival_time TEXT, passenger_count INTEGER,
                  transfer_passengers INTEGER, gate_preferences TEXT, required_services TEXT,
                  minimum_ground_time_minutes INTEGER, priority_level INTEGER, special_requirements TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS weather_conditions
                 (timestamp TEXT, condition TEXT, temperature_celsius REAL, 
                  wind_speed_kmh REAL, visibility_km REAL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS runway_status
                 (runway_id TEXT, length_meters INTEGER, current_status TEXT, 
                  scheduled_maintenance TEXT, arrivals_per_hour INTEGER, departures_per_hour INTEGER)''')

    conn.commit()
    return conn

def insert_airport_data(conn, airport_data):
    c = conn.cursor()
    c.execute("INSERT INTO airport VALUES (?, ?, ?, ?)", 
              (airport_data['name'], airport_data['IATA_code'], 
               airport_data['ICAO_code'], airport_data['time_zone']))
    conn.commit()

def insert_terminals(conn, terminals):
    c = conn.cursor()
    c.executemany("INSERT INTO terminals VALUES (?, ?, ?)", 
                  [(t['terminal_id'], t['description'], t['capacity']) for t in terminals])
    conn.commit()

def insert_gates(conn):
    c = conn.cursor()
    gates = []
    for terminal in datagen.IGI_PARAMS['terminals']:
        for i in range(1, datagen.IGI_PARAMS['gates'][terminal['terminal_id']] + 1):
            gate_id = f"{terminal['terminal_id']}-{i}"
            aircraft_compatibility = json.dumps(random.sample(list(datagen.IGI_PARAMS['aircraft_types'].keys()), k=random.randint(2, 4)))
            boarding_bridge = random.choice([0, 1])
            remote_stand = 1 - boarding_bridge
            max_passengers = random.choice([200, 300, 400, 500])
            gates.append((gate_id, terminal['terminal_id'], aircraft_compatibility, boarding_bridge, remote_stand, max_passengers))
    
    c.executemany("INSERT INTO gates VALUES (?, ?, ?, ?, ?, ?)", gates)
    conn.commit()

def insert_airlines(conn, airlines):
    c = conn.cursor()
    c.executemany("INSERT INTO airlines VALUES (?)", [(airline,) for airline in airlines])
    conn.commit()

def insert_aircraft_types(conn, aircraft_types):
    c = conn.cursor()
    c.executemany("INSERT INTO aircraft_types VALUES (?, ?, ?, ?, ?)",
                  [(type, data['wingspan'], data['length'], data['height'], data['weight']) 
                   for type, data in aircraft_types.items()])
    conn.commit()

def insert_flights(conn, flights):
    c = conn.cursor()
    for flight in flights:
        c.execute('''INSERT INTO flights VALUES 
                     (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                  (flight['flight_id'], flight['airline'], flight['aircraft_type'],
                   flight['origin'], flight['destination'], flight['flight_type'],
                   flight['scheduled_departure_time'], flight['scheduled_arrival_time'],
                   flight['estimated_departure_time'], flight['estimated_arrival_time'],
                   flight['passenger_count'], flight['transfer_passengers'],
                   json.dumps(flight['gate_preferences']),
                   json.dumps(flight['required_services']),
                   flight['minimum_ground_time_minutes'], flight['priority_level'],
                   json.dumps(flight['special_requirements'])))
    conn.commit()

def insert_weather_conditions(conn, weather_conditions):
    c = conn.cursor()
    c.executemany('''INSERT INTO weather_conditions VALUES (?, ?, ?, ?, ?)''', 
                  [(w['timestamp'], w['condition'], w['temperature_celsius'],
                    w['wind_speed_kmh'], w['visibility_km']) for w in weather_conditions])
    conn.commit()

def insert_runway_status(conn, runway_status):
    c = conn.cursor()
    c.executemany('''INSERT INTO runway_status VALUES (?, ?, ?, ?, ?, ?)''', 
                  [(r['runway_id'], r['length_meters'], r['current_status'],
                    r['scheduled_maintenance'], r['arrivals_per_hour'], r['departures_per_hour']) 
                   for r in runway_status])
    conn.commit()

def main():
    conn = create_database()

    # Generate data
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    num_days = 7
    flights = datagen.generate_flights(start_date, num_days)
    weather_conditions = datagen.generate_weather_conditions(start_date, num_days)
    runway_status = datagen.generate_runway_status()

    # Insert data into database
    insert_airport_data(conn, datagen.IGI_PARAMS['airport'])
    insert_terminals(conn, datagen.IGI_PARAMS['terminals'])
    insert_gates(conn)
    insert_airlines(conn, datagen.IGI_PARAMS['airlines'])
    insert_aircraft_types(conn, datagen.IGI_PARAMS['aircraft_types'])
    insert_flights(conn, flights)
    insert_weather_conditions(conn, weather_conditions)
    insert_runway_status(conn, runway_status)

    conn.close()

    print("Data generation and database creation complete. Check 'igi_airport_data.db' for the result.")

if __name__ == "__main__":
    main()