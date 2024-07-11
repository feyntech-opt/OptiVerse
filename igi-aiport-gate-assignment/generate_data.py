import random
from datetime import datetime, timedelta

# IGI Airport-specific parameters
IGI_PARAMS = {
    "airport": {
        "name": "Indira Gandhi International Airport",
        "IATA_code": "DEL",
        "ICAO_code": "VIDP",
        "time_zone": "Asia/Kolkata"
    },
    "terminals": [
        {"terminal_id": "T1", "description": "Domestic Terminal", "capacity": 20000000},  # Annual passenger capacity
        {"terminal_id": "T2", "description": "Domestic Terminal", "capacity": 15000000},
        {"terminal_id": "T3", "description": "International and Domestic Terminal", "capacity": 40000000}
    ],
    "gates": {
        "T1": 20,
        "T2": 20,
        "T3": 78  # T3 has more gates as it's the largest terminal
    },
    "airlines": [
        "Air India", "IndiGo", "SpiceJet", "Vistara", "GoAir", "AirAsia India",  # Major domestic airlines
        "Emirates", "Lufthansa", "British Airways", "Singapore Airlines", "Qatar Airways", "Etihad Airways"  # Major international airlines
    ],
    "aircraft_types": {
        "A320": {"wingspan": 35.8, "length": 37.6, "height": 11.8, "weight": 78},
        "B737": {"wingspan": 35.9, "length": 39.5, "height": 12.5, "weight": 79},
        "A330": {"wingspan": 60.3, "length": 63.7, "height": 16.8, "weight": 242},
        "B777": {"wingspan": 64.8, "length": 73.9, "height": 18.5, "weight": 351},
        "A350": {"wingspan": 64.8, "length": 66.8, "height": 17.1, "weight": 280},
        "B787": {"wingspan": 60.1, "length": 62.8, "height": 17.0, "weight": 228}
    },
    "daily_flights": {
        "range": (1000, 1300)  # IGI handles about 1200 flights per day
    },
    "flight_distribution": {
        "domestic": 0.7,  # 70% domestic flights
        "international": 0.3  # 30% international flights
    },
    "popular_domestic_routes": [
        "BOM", "BLR", "HYD", "MAA", "CCU", "PNQ", "AMD", "GOI", "LKO", "PAT"
    ],
    "popular_international_routes": [
        "DXB", "LHR", "SIN", "BKK", "AUH", "HKG", "FRA", "KUL", "JFK", "DOH"
    ],
    "ground_services": [
        "catering", "cleaning", "refueling", "maintenance", "baggage_handling", "water_service", "lavatory_service"
    ],
    "runways": [
        {"runway_id": "09/27", "length": 3810},
        {"runway_id": "10/28", "length": 4430},
        {"runway_id": "11/29", "length": 4430}
    ],
    "weather": {
        "summer": {
            "months": [4, 5, 6, 7, 8, 9],  # April to September
            "temperature_range": (25, 45),
            "conditions": ["Clear", "Partly Cloudy", "Haze", "Dust"]
        },
        "winter": {
            "months": [10, 11, 12, 1, 2, 3],  # October to March
            "temperature_range": (5, 25),
            "conditions": ["Clear", "Partly Cloudy", "Fog", "Rain"]
        }
    },
    "operational_constraints": {
        "minimum_connection_time_minutes": {
            "domestic_to_domestic": 45,
            "domestic_to_international": 60,
            "international_to_domestic": 75,
            "international_to_international": 90
        },
        "maximum_walking_distance_meters": 800,
        "gate_conflict_buffer_minutes": 30,
        "remote_stand_transfer_time_minutes": 15
    },
    "optimization_objectives": [
        {"objective": "minimize_passenger_walking_distance", "weight": 0.3},
        {"objective": "maximize_gate_utilization", "weight": 0.25},
        {"objective": "minimize_connection_times", "weight": 0.2},
        {"objective": "minimize_airline_preference_violations", "weight": 0.15},
        {"objective": "minimize_towing_operations", "weight": 0.1}
    ]
}

def generate_flights(start_date, num_days):
    flights = []
    current_date = start_date
    for _ in range(num_days):
        num_flights = random.randint(*IGI_PARAMS["daily_flights"]["range"])
        for _ in range(num_flights):
            is_domestic = random.random() < IGI_PARAMS["flight_distribution"]["domestic"]
            airline = random.choice(IGI_PARAMS["airlines"])
            aircraft_type = random.choice(list(IGI_PARAMS["aircraft_types"].keys()))
            
            if is_domestic:
                origin = "DEL" if random.random() < 0.5 else random.choice(IGI_PARAMS["popular_domestic_routes"])
                destination = random.choice(IGI_PARAMS["popular_domestic_routes"]) if origin == "DEL" else "DEL"
            else:
                origin = "DEL" if random.random() < 0.5 else random.choice(IGI_PARAMS["popular_international_routes"])
                destination = random.choice(IGI_PARAMS["popular_international_routes"]) if origin == "DEL" else "DEL"
            
            departure_time = current_date + timedelta(minutes=random.randint(0, 1439))
            flight_duration = timedelta(minutes=random.randint(60, 600))
            arrival_time = departure_time + flight_duration
            
            flight = {
                "flight_id": f"{airline[:2]}{random.randint(100, 9999)}",
                "airline": airline,
                "aircraft_type": aircraft_type,
                "origin": origin,
                "destination": destination,
                "flight_type": "departure" if origin == "DEL" else "arrival",
                "scheduled_departure_time": departure_time.isoformat(),
                "scheduled_arrival_time": arrival_time.isoformat(),
                "estimated_departure_time": (departure_time + timedelta(minutes=random.randint(-15, 30))).isoformat(),
                "estimated_arrival_time": (arrival_time + timedelta(minutes=random.randint(-15, 30))).isoformat(),
                "passenger_count": random.randint(50, int(IGI_PARAMS["aircraft_types"][aircraft_type]["weight"] * 2)),
                "transfer_passengers": random.randint(0, 50) if not is_domestic else 0,
                "gate_preferences": [f"T{'3' if not is_domestic else random.choice(['1', '2', '3'])}-{random.randint(1, IGI_PARAMS['gates']['T3'])}" for _ in range(3)],
                "required_services": random.sample(IGI_PARAMS["ground_services"], k=random.randint(2, 5)),
                "minimum_ground_time_minutes": random.randint(30, 120),
                "priority_level": random.randint(1, 5),
                "special_requirements": random.sample(["wheelchair", "unaccompanied_minor", "oversized_baggage"], k=random.randint(0, 2))
            }
            flights.append(flight)
        current_date += timedelta(days=1)
    return flights

def generate_weather_conditions(start_date, num_days):
    conditions = []
    current_date = start_date
    for _ in range(num_days):
        month = current_date.month
        if month in IGI_PARAMS["weather"]["summer"]["months"]:
            temp_range = IGI_PARAMS["weather"]["summer"]["temperature_range"]
            possible_conditions = IGI_PARAMS["weather"]["summer"]["conditions"]
        else:
            temp_range = IGI_PARAMS["weather"]["winter"]["temperature_range"]
            possible_conditions = IGI_PARAMS["weather"]["winter"]["conditions"]
        
        for _ in range(24):  # Hourly weather data
            condition = {
                "timestamp": current_date.isoformat(),
                "condition": random.choice(possible_conditions),
                "temperature_celsius": random.uniform(*temp_range),
                "wind_speed_kmh": random.uniform(0, 30),
                "visibility_km": random.uniform(1, 10)
            }
            conditions.append(condition)
            current_date += timedelta(hours=1)
    return conditions

def generate_runway_status():
    return [
        {
            "runway_id": runway["runway_id"],
            "length_meters": runway["length"],
            "current_status": random.choice(["operational", "maintenance", "closed"]),
            "scheduled_maintenance": (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat() if random.random() < 0.1 else None,
            "arrivals_per_hour": random.randint(20, 30),
            "departures_per_hour": random.randint(20, 30)
        } for runway in IGI_PARAMS["runways"]
    ]

# Example usage
start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
num_days = 7

flights = generate_flights(start_date, num_days)
weather_conditions = generate_weather_conditions(start_date, num_days)
runway_status = generate_runway_status()

print(f"Generated {len(flights)} flights for {num_days} days")
print(f"Generated {len(weather_conditions)} hourly weather conditions")
print(f"Generated runway status for {len(runway_status)} runways")

# You can now use these generated data sets in your main simulation script