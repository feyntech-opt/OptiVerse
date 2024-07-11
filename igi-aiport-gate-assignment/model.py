import csv
import sqlite3
from ortools.sat.python import cp_model
from datetime import datetime, timedelta
import logging
from database_manager import create_engine, sessionmaker, Flight

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def create_gate_assignment_model(db_path, start_time, end_time):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch flights, gates, and compatibility data
    cursor.execute("""
        SELECT f.id, f.airline, f.aircraft_registration, f.origin, f.destination,
               strftime('%Y-%m-%d %H:%M:%S', f.scheduled_arrival) as scheduled_arrival, 
               strftime('%Y-%m-%d %H:%M:%S', f.scheduled_departure) as scheduled_departure, 
               f.passenger_count, a.type, f.connecting_flight_id
        FROM flights f
        JOIN aircraft a ON f.aircraft_registration = a.registration
        WHERE (f.scheduled_arrival BETWEEN ? AND ?)
           OR (f.scheduled_departure BETWEEN ? AND ?)
           OR (f.scheduled_arrival <= ? AND f.scheduled_departure >= ?)
        ORDER BY f.scheduled_departure
    """, (start_time, end_time, start_time, end_time, start_time, end_time))
    
    flights = cursor.fetchall()

    cursor.execute("SELECT id, terminal_id, max_passengers FROM gates")
    gates = cursor.fetchall()

    cursor.execute("SELECT DISTINCT gate_id, aircraft_type FROM gate_aircraft_compatibility")
    gate_aircraft_compatibility = cursor.fetchall()

    # Fetch transit times
    cursor.execute("SELECT from_location, to_location, transport_type, time_minutes FROM transit_times")
    transit_times = {(row[0], row[1], row[2]): row[3] for row in cursor.fetchall()}

    logging.info(f"Fetched {len(flights)} flights and {len(gates)} gates.")

    # Create compatibility dictionary
    compatible_gates = {flight[8]: set() for flight in flights}
    for gate_id, aircraft_type in gate_aircraft_compatibility:
        if aircraft_type in compatible_gates:
            compatible_gates[aircraft_type].add(gate_id)

    model = cp_model.CpModel()

    # Create variables
    gate_assignments = {}
    for i, flight in enumerate(flights):
        for j, gate in enumerate(gates):
            gate_assignments[(i, j)] = model.NewBoolVar(f'f{i}_g{j}')

    # Constraints
    # Each flight must be assigned to exactly one gate
    for i in range(len(flights)):
        model.Add(sum(gate_assignments[(i, j)] for j in range(len(gates))) == 1)

    # Each gate can be assigned to at most one flight at a time
    for j in range(len(gates)):
        for i1 in range(len(flights)):
            for i2 in range(i1 + 1, len(flights)):
                flight1 = flights[i1]
                flight2 = flights[i2]
                if (flight1[5] < flight2[6] and flight2[5] < flight1[6]):  # Overlap check
                    model.Add(gate_assignments[(i1, j)] + gate_assignments[(i2, j)] <= 1)

    # Compatibility constraints
    for i, flight in enumerate(flights):
        for j, gate in enumerate(gates):
            if gate[0] not in compatible_gates.get(flight[8], set()):
                model.Add(gate_assignments[(i, j)] == 0)

    # Terminal balancing
    terminal_usage = {}
    for terminal in set(gate[1] for gate in gates):
        terminal_usage[terminal] = model.NewIntVar(0, len(flights), f'usage_{terminal}')
        model.Add(terminal_usage[terminal] == sum(gate_assignments[(i, j)]
                                                  for i in range(len(flights))
                                                  for j, gate in enumerate(gates) if gate[1] == terminal))

    max_terminal_usage = model.NewIntVar(0, len(flights), 'max_terminal_usage')
    min_terminal_usage = model.NewIntVar(0, len(flights), 'min_terminal_usage')
    model.AddMaxEquality(max_terminal_usage, list(terminal_usage.values()))
    model.AddMinEquality(min_terminal_usage, list(terminal_usage.values()))

    terminal_usage_difference = model.NewIntVar(0, len(flights), 'terminal_usage_difference')
    model.Add(terminal_usage_difference == max_terminal_usage - min_terminal_usage)

    # Gate usage balancing
    gate_usage = [model.NewIntVar(0, len(flights), f'gate_usage_{j}') for j in range(len(gates))]
    for j in range(len(gates)):
        model.Add(gate_usage[j] == sum(gate_assignments[(i, j)] for i in range(len(flights))))

    max_gate_usage = model.NewIntVar(0, len(flights), 'max_gate_usage')
    min_gate_usage = model.NewIntVar(0, len(flights), 'min_gate_usage')
    model.AddMaxEquality(max_gate_usage, gate_usage)
    model.AddMinEquality(min_gate_usage, gate_usage)

    gate_usage_difference = model.NewIntVar(0, len(flights), 'gate_usage_difference')
    model.Add(gate_usage_difference == max_gate_usage - min_gate_usage)

    # Airline preferences (soft constraint)
    airline_preferences = {
        'AI': 'T3',  # Air India prefers Terminal 3
        '6E': 'T1',  # IndiGo prefers Terminal 1
        'UK': 'T3',  # Vistara prefers Terminal 3
        'SG': 'T1',  # SpiceJet prefers Terminal 1
    }
    preference_violations = []
    for i, flight in enumerate(flights):
        airline = flight[1]
        if airline in airline_preferences:
            preferred_terminal = airline_preferences[airline]
            for j, gate in enumerate(gates):
                if not gate[1].startswith(preferred_terminal):
                    violation = model.NewBoolVar(f'pref_violation_{i}_{j}')
                    model.Add(gate_assignments[(i, j)] <= violation)
                    preference_violations.append(violation)

    # Transit time constraints
    total_transit_time = model.NewIntVar(0, 10000000, 'total_transit_time')  # Arbitrary large upper bound
    transit_times_list = []
    for i, flight in enumerate(flights):
        if flight[9]:  # If there's a connecting flight
            connecting_flight_index = next((idx for idx, f in enumerate(flights) if f[0] == flight[9]), None)
            if connecting_flight_index is not None:
                for j1, gate1 in enumerate(gates):
                    for j2, gate2 in enumerate(gates):
                        transit_time = model.NewIntVar(0, 1000, f'transit_time_{i}_{connecting_flight_index}_{j1}_{j2}')
                        transit_times_list.append(transit_time)
                        
                        # Get the transit time between gates, default to 30 minutes if not found
                        time_between_gates = transit_times.get((gate1[0], gate2[0], 'PASSENGER'), 30)
                        
                        model.Add(transit_time >= time_between_gates).OnlyEnforceIf(
                            [gate_assignments[(i, j1)], gate_assignments[(connecting_flight_index, j2)]]
                        )
                        model.Add(transit_time == 0).OnlyEnforceIf(
                            [gate_assignments[(i, j1)].Not(), gate_assignments[(connecting_flight_index, j2)].Not()]
                        )

    model.Add(total_transit_time == sum(transit_times_list))

    # Passenger count considerations
    total_passengers = model.NewIntVar(0, sum(flight[7] for flight in flights), 'total_passengers')
    model.Add(total_passengers == sum(gate_assignments[(i, j)] * flight[7] for i, flight in enumerate(flights) for j in range(len(gates))))

    # Objective function components
    total_assigned = sum(gate_assignments[(i, j)] for i in range(len(flights)) for j in range(len(gates)))
    total_preference_violations = sum(preference_violations)

    # Objective: Maximize assignments, minimize usage differences, maximize passengers, minimize preference violations and transit times
    model.Maximize(1000000 * total_assigned + 10000 * total_passengers - 1000 * terminal_usage_difference - 
                   100 * gate_usage_difference - 500 * total_preference_violations - total_transit_time)

    # Solve the model
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300.0
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        logging.info(f'Solution found with status: {solver.StatusName(status)}')
        assignments = [(flight[0], flight[1], gates[j][0], flight[5], flight[6], flight[7])
                       for i, flight in enumerate(flights)
                       for j in range(len(gates))
                       if solver.Value(gate_assignments[(i, j)]) == 1]
        
        # Log results
        logging.info(f"Total flights assigned: {len(assignments)}")
        logging.info(f"Total passengers accommodated: {solver.Value(total_passengers)}")
        logging.info(f"Terminal usage difference: {solver.Value(terminal_usage_difference)}")
        logging.info(f"Gate usage difference: {solver.Value(gate_usage_difference)}")
        logging.info(f"Airline preference violations: {solver.Value(total_preference_violations)}")
        logging.info(f"Total transit time: {solver.Value(total_transit_time)}")
        
        for terminal, usage in terminal_usage.items():
            logging.info(f"Terminal {terminal} usage: {solver.Value(usage)}")
        
        # Generate CSV file
        csv_filename = 'gate_assignments.csv'
        with open(csv_filename, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['Flight ID', 'Airline', 'Gate', 'Arrival Time', 'Departure Time', 'Passengers'])
            for assignment in assignments:
                csvwriter.writerow(assignment)
        
        logging.info(f"Gate assignments saved to {csv_filename}")
        
        return assignments
    else:
        logging.warning(f'No solution found. Status: {solver.StatusName(status)}')
        return None
    
def main():
    db_path = 'igi_airport.db'
    
    # Connect to the database
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Query the database to find the earliest and latest flight times
    earliest_flight = session.query(Flight).order_by(Flight.scheduled_departure).first()
    latest_flight = session.query(Flight).order_by(Flight.scheduled_arrival.desc()).first()

    if earliest_flight and latest_flight:
        # Set the start time to the earliest flight's departure time
        start_time = earliest_flight.scheduled_departure
        # Set the end time to 24 hours after the start time
        end_time = start_time + timedelta(hours=24)

        print(f"Analyzing flights from {start_time} to {end_time}")

        assignments = create_gate_assignment_model(db_path, start_time.isoformat(), end_time.isoformat())

        if assignments:
            print(f"Gate assignments have been saved to gate_assignments.csv")
            print(f"Total flights assigned: {len(assignments)}")
        else:
            print("No assignments could be made.")
    else:
        print("No flights found in the database.")

    session.close()

if __name__ == "__main__":
    main()