import sqlite3

def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return any(row[1] == column_name for row in cursor.fetchall())

def create_enhanced_database():
    conn = sqlite3.connect('igi_airport_data.db')
    c = conn.cursor()

    # Check and add column to gates table
    if not column_exists(c, 'gates', 'terminal_location'):
        c.execute('ALTER TABLE gates ADD COLUMN terminal_location TEXT')

    # Create aircraft table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS aircraft
                 (registration TEXT PRIMARY KEY, type TEXT, 
                  next_maintenance_due TEXT)''')

    # Check and add columns to flights table
    if not column_exists(c, 'flights', 'aircraft_registration'):
        c.execute('ALTER TABLE flights ADD COLUMN aircraft_registration TEXT')
    
    if not column_exists(c, 'flights', 'connecting_flight_id'):
        c.execute('ALTER TABLE flights ADD COLUMN connecting_flight_id TEXT')

    conn.commit()
    return conn

# The rest of your script remains the same...

def main():
    conn = create_enhanced_database()

    # Generate new data
    generate_aircraft(conn, 100)  # Generate 100 aircraft
    update_gates_with_location(conn)
    update_flights_with_aircraft_and_connections(conn)

    conn.close()
    print("Enhanced data generation complete. Check 'igi_airport_data.db' for the result.")

if __name__ == "__main__":
    main()