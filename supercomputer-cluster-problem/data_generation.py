import random
import json

def generate_country_data():
    countries = [
        'USA', 'China', 'Russia', 'EU', 'India', 'Japan',
        'South Korea', 'Canada', 'Australia', 'Israel'
    ]

    country_data = {}

    for country in countries:
        gdp = random.randint(500, 20000)  # GDP in billions of dollars
        population = random.randint(10, 1400)  # Population in millions
        tech_investment = random.uniform(1, 5)  # Percentage of GDP invested in tech
        education_index = random.uniform(0.5, 1)  # Education index (0-1)
        
        country_data[country] = {
            'gdp': gdp,
            'population': population,
            'tech_investment': tech_investment,
            'education_index': education_index,
            'initial_tech_level': random.randint(70, 95),
            'initial_resources': random.randint(70, 100)
        }

    return country_data

def save_country_data(data, filename='country_data.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def load_country_data(filename='country_data.json'):
    with open(filename, 'r') as f:
        return json.load(f)

if __name__ == "__main__":
    country_data = generate_country_data()
    save_country_data(country_data)
    print("Country data generated and saved to country_data.json")
