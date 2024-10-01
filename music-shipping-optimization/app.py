import streamlit as st
import json
import random
import math
from ortools.sat.python import cp_model
import pandas as pd


# Define trucks
trucks = [
    {"type": "Small Truck", "dimensions": {"length": 300, "width": 150, "height": 150}, "max_volume": 6.75, "max_weight": 1000},
    {"type": "Medium Truck", "dimensions": {"length": 500, "width": 200, "height": 200}, "max_volume": 20, "max_weight": 3000},
    {"type": "Large Truck", "dimensions": {"length": 800, "width": 250, "height": 250}, "max_volume": 50, "max_weight": 7000},
] * 10  # Assume 10 trucks available

# Function to load and simulate data
def simulate_orders(num_orders, instruments, warehouses, parameters):
    orders = []
    for _ in range(num_orders):
        instrument = random.choice(instruments)
        city = random.choice(parameters['destination_cities'])
        warehouse = next(wh for wh in warehouses if wh['city'] == city)

        lat = warehouse['latitude'] + random.uniform(-parameters['max_coordinate_offset'], parameters['max_coordinate_offset'])
        lon = warehouse['longitude'] + random.uniform(-parameters['max_coordinate_offset'], parameters['max_coordinate_offset'])

        express = random.random() < parameters['probability_express_delivery']

        order = {
            "instrument": instrument["instrument"],
            "dimensions": instrument["dimensions"],
            "weight": int(instrument["weight"]),  # Ensure weight is integer
            "stackable": instrument["stackable"],
            "fragile": instrument["fragile"],
            "destination": {
                "city": city,
                "latitude": lat,
                "longitude": lon
            },
            "express_delivery": express
        }
        orders.append(order)

    return orders

# Haversine distance function
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def create_cp_model(orders, trucks):
    model = cp_model.CpModel()
    num_orders = len(orders)
    num_trucks = len(trucks)

    X = {}  # X[i, j] is 1 if order i is assigned to truck j
    Y = []  # Y[j] is 1 if truck j is used
    Z = {}  # Z[j, i, k] is 1 if truck j travels directly from order i to order k
    S = {}  # S[i, k, j] is 1 if item i is stacked on top of item k in truck j

    for i in range(num_orders):
        for j in range(num_trucks):
            X[i, j] = model.NewBoolVar(f'X_{i}_{j}')
            for k in range(num_orders):
                if i != k:
                    Z[j, i, k] = model.NewBoolVar(f'Z_{j}_{i}_{k}')
                    S[i, k, j] = model.NewBoolVar(f'S_{i}_{k}_{j}')

    for j in range(num_trucks):
        Y.append(model.NewBoolVar(f'Y_{j}'))

    # Constraints
    for i in range(num_orders):
        model.Add(sum(X[i, j] for j in range(num_trucks)) == 1)

    for j in range(num_trucks):
        order_volumes = [
            X[i, j] * (
                orders[i]["dimensions"]["length"] *
                orders[i]["dimensions"]["width"] *
                orders[i]["dimensions"]["height"]
            ) for i in range(num_orders)
        ]
        max_volume_cm3 = int(trucks[j]["max_volume"] * 1000000)
        model.Add(sum(order_volumes) <= max_volume_cm3 * Y[j])
        model.Add(
            sum(X[i, j] * orders[i]["weight"] for i in range(num_orders)) <= trucks[j]["max_weight"] * Y[j]
        )

        # Stackable and Fragile Constraints
        for i in range(num_orders):
            for k in range(num_orders):
                if i != k:
                    # If order i is stacked on k, then both must be in the same truck
                    model.Add(S[i, k, j] <= X[i, j])
                    model.Add(S[i, k, j] <= X[k, j])
                    # Non-stackable items cannot have any other item on top
                    if not orders[k]["stackable"]:
                        model.Add(S[i, k, j] == 0)
                    # Fragile items cannot have any other item on top
                    if orders[k]["fragile"]:
                        model.Add(S[i, k, j] == 0)

        # Circuit constraint for each truck
        circuit_arcs = []
        for i in range(num_orders):
            for k in range(num_orders):
                if i != k:
                    circuit_arcs.append([i, k, Z[j, i, k]])

        model.AddCircuit(circuit_arcs)

    # Objective: Minimize total Haversine distance traveled by all trucks
    total_distance = []
    for j in range(num_trucks):
        for i in range(num_orders):
            for k in range(num_orders):
                if i != k:
                    dist = haversine(
                        orders[i]["destination"]["latitude"], orders[i]["destination"]["longitude"],
                        orders[k]["destination"]["latitude"], orders[k]["destination"]["longitude"]
                    )
                    total_distance.append(Z[j, i, k] * dist)
    model.Minimize(sum(total_distance))

    return model, X, Y, Z, S



def solve_model(model, X, Y, Z, S, num_orders, num_trucks, num_solutions=1):
    solver = cp_model.CpSolver()
    solutions = []

    solver.parameters.max_time_in_seconds = 20

    class VarArraySolutionPrinter(cp_model.CpSolverSolutionCallback):
        def __init__(self, X, Y, Z, S, num_orders, num_trucks, solutions, num_solutions):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self._X = X
            self._Y = Y
            self._Z = Z
            self._S = S
            self._num_orders = num_orders
            self._num_trucks = num_trucks
            self._solutions = solutions
            self._num_solutions = num_solutions
            self._solution_count = 0

        def on_solution_callback(self):
            if self._solution_count < self._num_solutions:
                solution = {}
                for j in range(self._num_trucks):
                    if self.Value(self._Y[j]) == 1:
                        truck_load = []
                        truck_path = []
                        for i in range(self._num_orders):
                            if self.Value(self._X[i, j]) == 1:
                                truck_load.append(i)
                        
                        # Determine the path for the truck
                        if truck_load:
                            current_order = truck_load[0]  # Start with the first order in the list
                            truck_path.append(current_order)
                            visited = {current_order}
                            while len(visited) < len(truck_load):
                                for k in truck_load:
                                    if k not in visited and self.Value(self._Z[j, current_order, k]) == 1:
                                        visited.add(k)
                                        truck_path.append(k)
                                        current_order = k
                                        break

                        # Stacking information
                        stacking_info = []
                        for i in truck_load:
                            for k in truck_load:
                                if i != k and self.Value(self._S[i, k, j]) == 1:
                                    stacking_info.append({"Order": i, "Stacked On": k})
                                else:
                                    stacking_info.append({"Order": i, "Stacked On": "None"})

                        solution[f'Truck_{j+1}'] = {
                            "orders": truck_load,
                            "path": truck_path,
                            "stacking": stacking_info
                        }

                self._solutions.append(solution)
                self._solution_count += 1


    solution_printer = VarArraySolutionPrinter(X, Y, Z, S, num_orders, num_trucks, solutions, num_solutions)
    solver.SolveWithSolutionCallback(model, solution_printer)

    return solutions


# Streamlit UI
st.title("Logistics Optimization for HarmonyHub")

st.sidebar.header("Simulation Parameters")
num_orders = st.sidebar.slider("Number of Orders", 10, 100, 50)
num_solutions = st.sidebar.slider("Number of Solutions", 1, 10, 1)

# Load instrument and warehouse data (simulated here)
instruments = [
    {"instrument": "Grand Piano", "dimensions": {"length": 150, "width": 180, "height": 100}, "weight": 500, "stackable": False, "fragile": True},
    {"instrument": "Drum Set", "dimensions": {"length": 100, "width": 100, "height": 120}, "weight": 40, "stackable": True, "fragile": True},
    {"instrument": "Electric Guitar", "dimensions": {"length": 110, "width": 40, "height": 15}, "weight": 7, "stackable": True, "fragile": True},
    {"instrument": "Cello", "dimensions": {"length": 130, "width": 50, "height": 25}, "weight": 12, "stackable": True, "fragile": True},
    {"instrument": "Violin", "dimensions": {"length": 60, "width": 20, "height": 10}, "weight": 1.5, "stackable": True, "fragile": True},
    {"instrument": "Trumpet", "dimensions": {"length": 50, "width": 15, "height": 20}, "weight": 3, "stackable": True, "fragile": True},
    {"instrument": "Saxophone", "dimensions": {"length": 70, "width": 25, "height": 20}, "weight": 5, "stackable": True, "fragile": True},
    {"instrument": "Flute", "dimensions": {"length": 70, "width": 10, "height": 10}, "weight": 1, "stackable": True, "fragile": False},
    {"instrument": "Double Bass", "dimensions": {"length": 200, "width": 80, "height": 60}, "weight": 50, "stackable": False, "fragile": True},
    {"instrument": "Keyboard", "dimensions": {"length": 150, "width": 50, "height": 15}, "weight": 20, "stackable": True, "fragile": True},
]

warehouses = [
    {"city": "Pune", "latitude": 18.5204, "longitude": 73.8567, "capacity": 1000},
    {"city": "Mumbai", "latitude": 19.0760, "longitude": 72.8777, "capacity": 1500},
]


parameters = {
    "probability_express_delivery": 0.2,
    "pune_coordinates": {"latitude": 18.5204, "longitude": 73.8567},
    "mumbai_coordinates": {"latitude": 19.0760, "longitude": 72.8777},
    "max_coordinate_offset": 0.05,
    "destination_cities": ["Pune", "Mumbai"]
}

# Button to simulate data
if st.button("Simulate Data"):
    orders = simulate_orders(num_orders, instruments, warehouses, parameters)
    st.session_state['orders'] = orders  # Store orders in session state
    st.json(orders)

def display_solutions(solutions, orders, trucks):
    if solutions:
        for idx, solution in enumerate(solutions):
            with st.expander(f"Solution {idx+1}"):
                total_distance = 0
                total_orders = 0
                for truck_id, data in solution.items():
                    st.subheader(f"{truck_id} - {trucks[int(truck_id.split('_')[1])-1]['type']}")
                    
                    # Display truck details
                    st.write(f"Max Volume: {trucks[int(truck_id.split('_')[1])-1]['max_volume']} m³")
                    st.write(f"Max Weight: {trucks[int(truck_id.split('_')[1])-1]['max_weight']} kg")
                    
                    # Calculate and display KPIs
                    truck_distance = sum(haversine(
                        orders[data['path'][i]]["destination"]["latitude"],
                        orders[data['path'][i]]["destination"]["longitude"],
                        orders[data['path'][i+1]]["destination"]["latitude"],
                        orders[data['path'][i+1]]["destination"]["longitude"]
                    ) for i in range(len(data['path']) - 1))
                    
                    total_distance += truck_distance
                    total_orders += len(data['orders'])
                    
                    st.write(f"Orders: {len(data['orders'])}")
                    st.write(f"Distance: {truck_distance:.2f} km")
                    
                    # Display path
                    st.table(pd.DataFrame(data['path'], columns=["Order"]))

                # Display overall KPIs
                st.subheader("Overall KPIs")
                st.write(f"Total Distance: {total_distance:.2f} km")
                st.write(f"Total Orders: {total_orders}")
                st.write(f"Average Distance per Order: {total_distance/total_orders:.2f} km")

# In the "Run Optimization" button callback
if st.button("Run Optimization"):
    if 'orders' in st.session_state:
        orders = st.session_state['orders']
        num_trucks = len(trucks)
        model, X, Y, Z, S = create_cp_model(orders, trucks)
        solutions = solve_model(model, X, Y, Z, S, num_orders, num_trucks, num_solutions)
        st.session_state['solutions'] = solutions
        display_solutions(solutions, orders, trucks)
    else:
        st.error("Please simulate data first by clicking 'Simulate Data'.")
