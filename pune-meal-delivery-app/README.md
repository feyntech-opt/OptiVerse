# Food Delivery Optimization Project

This project simulates and optimizes a food delivery system for Pune, India. It includes data generation, order assignment optimization using different models, and performance analysis over an hour-long period.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Files in the Project](#files-in-the-project)
3. [Setup and Installation](#setup-and-installation)
4. [Usage](#usage)
5. [Key Components](#key-components)
6. [Optimization Models](#optimization-models)
7. [Performance Metrics](#performance-metrics)
8. [Visualization](#visualization)
9. [Future Improvements](#future-improvements)

## Project Overview

This project simulates a food delivery system in Pune, India. It generates realistic data for restaurants, delivery agents, and orders, then uses optimization techniques to assign orders to agents efficiently. The system considers factors such as delivery time, distance, agent earnings, and customer ratings to make optimal assignments.

## Files in the Project

1. `simulate.py`: Generates simulated data for restaurants, agents, and orders.
2. `model.py`: Implements order assignment optimization using Gurobi.
3. `model_pulp.py`: Implements order assignment optimization using PuLP with CBC solver.
4. `hourly_model.py`: Implements hourly optimization and calculates key performance indicators (KPIs).

## Setup and Installation

1. Ensure you have Python 3.7+ installed.
2. Install required packages:
   ```
   pip install pandas numpy matplotlib seaborn pulp gurobipy
   ```
3. If using Gurobi, make sure you have a valid license and it's properly installed.

## Usage

1. Generate simulated data:

   ```
   python simulate.py
   ```

   This will create CSV files for restaurants, delivery agents, and orders.

2. Run the Gurobi optimization model for a single minute:

   ```
   python model.py
   ```

3. Run the PuLP optimization model for a single minute:

   ```
   python model_pulp.py
   ```

4. Run the hourly optimization with KPIs:
   ```
   python hourly_model.py
   ```
   This will generate assignment results, KPIs, and a visualization dashboard.

## Key Components

- **Data Generation** (`simulate.py`): Creates realistic data for restaurants, delivery agents, and orders in Pune.
- **Order Assignment** (`model.py`, `model_pulp.py`): Uses optimization techniques to assign orders to agents efficiently.
- **Agent Status Updates**: Updates agent locations and availability after each assignment.
- **KPI Calculation** (`hourly_model.py`): Computes various performance metrics to evaluate the system's efficiency over an hour.

## Optimization Models

The project includes two main optimization approaches:

1. **Gurobi Model** (`model.py`): Implements a mixed-integer programming model using Gurobi solver.
2. **PuLP Model** (`model_pulp.py`): Uses the PuLP library with the CBC solver for linear programming optimization.

Both models consider factors such as delivery time, distance, agent earnings, and customer ratings to make optimal assignments.

## Performance Metrics

The system calculates several key performance indicators (KPIs) in `hourly_model.py`:

- Order fulfillment rate
- Average delivery time
- Average delivery distance
- Agent utilization rate
- Revenue per minute and cumulative revenue

## Visualization

The `hourly_model.py` script includes a dashboard creation function that visualizes the KPIs using matplotlib and seaborn. The dashboard is saved as 'food_delivery_dashboard.png'.

## Future Improvements

1. Implement real-time optimization for a continuous stream of orders.
2. Add more sophisticated agent routing algorithms.
3. Incorporate machine learning for demand prediction and dynamic pricing.
4. Develop a web-based interface for real-time monitoring and control.
5. Extend the simulation to cover multiple cities or regions.
6. Implement a comparative analysis between Gurobi and PuLP optimization results.
7. Build a multi-objective model in PuLP, similar to the Gurobi implementation, to allow for fair comparison and leverage the open-source nature of PuLP.
8. Expand the dataset to cover a full week of operations, allowing for more comprehensive testing and analysis.
9. Test the robustness of the model under various disruption scenarios, such as:
   - High demand periods (e.g., weekends, holidays)
   - Traffic congestion
   - Adverse weather conditions (e.g., heavy rain)
   - Technical issues (e.g., app downtime)
10. Implement multi-pickup and multi-delivery features in the model to optimize for batched orders and increase efficiency.
11. Incorporate agents' working hours into the model, ensuring fair scheduling and compliance with labor regulations.
12. Optimize the last order assignment for each agent to drop them closer to their home location, improving agent satisfaction and reducing unnecessary travel.
13. Develop a more sophisticated agent earnings model that takes into account factors like distance traveled, time of day, and order complexity.

Feel free to contribute to this project by submitting pull requests or opening issues for any bugs or feature requests. We welcome collaboration on implementing these improvements and any other ideas that could enhance the food delivery optimization system.
