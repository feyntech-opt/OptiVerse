import sqlite3
from datetime import datetime, timedelta

def analyze_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get total number of flights
    cursor.execute("SELECT COUNT(*) FROM flights")
    total_flights = cursor.fetchone()[0]
    print(f"Total number of flights in the database: {total_flights}")

    # Get date range of flights
    cursor.execute("SELECT MIN(scheduled_departure), MAX(scheduled_arrival) FROM flights")
    min_date, max_date = cursor.fetchone()
    print(f"Date range of flights: from {min_date} to {max_date}")

    # Count flights per day
    cursor.execute("""
        SELECT DATE(scheduled_departure) as date, COUNT(*) as flight_count
        FROM flights
        GROUP BY DATE(scheduled_departure)
        ORDER BY date
    """)
    daily_counts = cursor.fetchall()
    print("\nFlights per day:")
    for date, count in daily_counts:
        print(f"{date}: {count} flights")

    # Count flights per airline
    cursor.execute("""
        SELECT airline, COUNT(*) as flight_count
        FROM flights
        GROUP BY airline
        ORDER BY flight_count DESC
    """)
    airline_counts = cursor.fetchall()
    print("\nFlights per airline:")
    for airline, count in airline_counts:
        print(f"{airline}: {count} flights")

    # Check for null values in important columns
    columns_to_check = ['id', 'airline', 'aircraft_registration', 'origin', 'destination', 
                        'scheduled_departure', 'scheduled_arrival', 'passenger_count']
    for column in columns_to_check:
        cursor.execute(f"SELECT COUNT(*) FROM flights WHERE {column} IS NULL")
        null_count = cursor.fetchone()[0]
        print(f"\nNull values in {column}: {null_count}")

    # Check for flights with invalid times (arrival before departure)
    cursor.execute("""
        SELECT COUNT(*) 
        FROM flights 
        WHERE scheduled_arrival < scheduled_departure
    """)
    invalid_times = cursor.fetchone()[0]
    print(f"\nFlights with arrival time before departure time: {invalid_times}")

    # Check for connecting flights
    cursor.execute("SELECT COUNT(*) FROM flights WHERE connecting_flight_id IS NOT NULL")
    connecting_flights = cursor.fetchone()[0]
    print(f"\nNumber of connecting flights: {connecting_flights}")

    conn.close()

if __name__ == "__main__":
    db_path = 'igi_airport.db'  # Update this path if necessary
    analyze_database(db_path)