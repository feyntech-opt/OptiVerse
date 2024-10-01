# main.py

from data_loader import load_data
from model import create_model
from optimizer import optimize_model
from config import *


def run_optimization():
    # Load data
    data = load_data()

    # Create model
    model, investment, capacity_slack, total_capacity_var, total_capacity_slack, source_used, total_production = create_model(
        data)

    # Optimize model
    results = optimize_model(model, data, investment, capacity_slack, total_capacity_var,
                             total_capacity_slack, source_used, total_production)

    if results:
        print_results(results)
    else:
        print("No optimal solution found.")


def print_results(results):
    print("\nOptimal solution found:")
    print(f"Total Investment: ₹{results['total_investment'] / 1e11:.2f} lakh crore")
    print(f"Total Capacity: {results['total_capacity']:.2f} MW")
    if results['capacity_shortfall'] > 0:
        print(f"Total Capacity Shortfall: {results['capacity_shortfall']:.2f} MW")

    print(f"Total Annual Production: {results['total_production']:.2f} TWh")
    print(f"Maximum Theoretical Annual Production: {results['max_theoretical_production']:.2f} TWh")

    print(
        f"Renewable Capacity: {results['renewable_capacity']:.2f} MW ({results['renewable_capacity']/results['total_capacity']*100:.2f}%)")

    print(f"Total Annual Emissions: {results['total_emissions']:.2f} kg CO2")
    print(f"Emissions Change: {results['emissions_change']:.2f}%")

    for s, data in results['source_investments'].items():
        print(f"\n{s}:")
        for y, inv in data['yearly_investments'].items():
            print(f"  {y}: ₹{inv / 1e11:.2f} lakh crore")
        print(f"  Total: ₹{data['total_investment'] / 1e11:.2f} lakh crore")
        print(f"  Capacity Addition: {data['capacity_addition']:.2f} MW")
        print(f"  Final Capacity: {data['final_capacity']:.2f} MW")
        print(f"  Capacity Factor: {data['capacity_factor']:.2f}")
        print(f"  Annual Production: {data['annual_production']:.2f} TWh")
        if data['min_capacity'] != 'N/A':
            print(f"  Min Capacity: {data['min_capacity']:.2f} MW")
        if data['max_capacity'] != 'N/A':
            print(f"  Max Capacity: {data['max_capacity']:.2f} MW")
        if data['capacity_shortfall'] > 0:
            print(f"  Capacity Shortfall: {data['capacity_shortfall']:.2f} MW")


if __name__ == "__main__":
    run_optimization()
