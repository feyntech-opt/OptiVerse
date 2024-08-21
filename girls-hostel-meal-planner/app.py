import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import gurobipy as gp
from gurobipy import GRB
import json
import plotly.graph_objects as go
import plotly.express as px
import re

# Import your optimizer function
from optimizer import create_optimizer_model, load_data

def run_optimization(data):
    model = create_optimizer_model(data)
    model.optimize()
    return model

def get_variable_values(model, prefix):
    return {v.varName: v.x for v in model.getVars() if v.varName.startswith(prefix)}

def create_schedule_df(schedule_dict, periods):
    # Extract item and day from variable names
    pattern = re.compile(r'(\w+)\[(\w+),(\d+)\]')
    data = []
    for var_name, value in schedule_dict.items():
        match = pattern.match(var_name)
        if match:
            var_type, item, day = match.groups()
            data.append({'Item': item, 'Day': int(day), 'Value': value})
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Pivot the DataFrame
    pivot_df = df.pivot(index='Item', columns='Day', values='Value')
    
    # Ensure all days up to the planning horizon are present
    for day in range(periods):
        if day not in pivot_df.columns:
            pivot_df[day] = 0
    
    # Sort columns and rename them
    pivot_df = pivot_df.sort_index(axis=1)
    pivot_df.columns = [f'Day {i+1}' for i in range(periods)]
    
    return pivot_df

def plot_inventory_levels(inventory_df):
    fig = px.line(inventory_df.T, title='Inventory Levels Over Time')
    fig.update_xaxes(title='Day')
    fig.update_yaxes(title='Inventory Level')
    return fig

def plot_purchase_schedule(purchase_df):
    fig = px.bar(purchase_df.T, title='Purchase Schedule')
    fig.update_xaxes(title='Day')
    fig.update_yaxes(title='Purchase Amount')
    return fig

def plot_delivery_schedule(delivery_schedule):
    fig = go.Figure(data=[go.Bar(x=list(range(1, len(delivery_schedule)+1)), 
                                 y=delivery_schedule,
                                 marker_color=['red' if x == 1 else 'blue' for x in delivery_schedule])])
    fig.update_layout(title='Delivery Schedule', xaxis_title='Day', yaxis_title='Delivery (1: Yes, 0: No)')
    return fig

def main():
    st.title('Dietary Supply Chain Optimizer Dashboard')

    # Load default data
    data = load_data('dietary_optimizer_data.json')

    # Sidebar for parameter adjustments
    st.sidebar.header('Adjust Parameters')
    
    # Allow user to adjust planning horizon
    horizon_days = st.sidebar.number_input('Planning Horizon (Days)', min_value=1, max_value=365, value=data['planning_info']['horizon_days'])
    data['planning_info']['horizon_days'] = horizon_days

    # Allow user to adjust number of people for each diet type
    st.sidebar.subheader('Number of People per Diet')
    for diet in data['diet_types']:
        data['diet_types'][diet]['num_people'] = st.sidebar.number_input(f'{diet.capitalize()} Diet', min_value=0, value=data['diet_types'][diet]['num_people'])

    # Allow user to adjust vehicle capacity
    data['logistic_info']['vehicle_capacity'] = st.sidebar.number_input('Vehicle Capacity', min_value=0, value=data['logistic_info']['vehicle_capacity'])

    if st.button('Run Optimization'):
        model = run_optimization(data)

        if model.status == GRB.OPTIMAL:
            st.success('Optimal solution found!')
            
            # Display objective value
            st.subheader('Total Cost')
            st.write(f'₹{model.objVal:.2f}')

            # Get and display slack variables
            st.subheader('Slack Variables')
            slack_vars = get_variable_values(model, 'ProteinSlack')
            if slack_vars:
                st.write(pd.DataFrame.from_dict(slack_vars, orient='index', columns=['Value']))
            else:
                st.write("No slack variables used in the solution.")

            # Inventory Levels
            inventory_vars = get_variable_values(model, 'Inventory')
            inventory_df = create_schedule_df(inventory_vars, data['planning_info']['horizon_days'])
            st.subheader('Inventory Levels')
            st.plotly_chart(plot_inventory_levels(inventory_df))

            # Purchase Schedule
            purchase_vars = get_variable_values(model, 'Purchase')
            purchase_df = create_schedule_df(purchase_vars, data['planning_info']['horizon_days'])
            st.subheader('Purchase Schedule')
            st.plotly_chart(plot_purchase_schedule(purchase_df))

            # Delivery Schedule
            delivery_vars = get_variable_values(model, 'Delivery')
            delivery_schedule = [delivery_vars.get(f'Delivery[{i}]', 0) for i in range(data['planning_info']['horizon_days'])]
            st.subheader('Delivery Schedule')
            st.plotly_chart(plot_delivery_schedule(delivery_schedule))

            # Nutritional Analysis
            st.subheader('Nutritional Analysis')
            for diet_type in data['diet_types']:
                st.write(f'**{diet_type.capitalize()} Diet**')
                protein_req = data['nutritional_info']['min_protein'][diet_type]
                carb_limit = data['nutritional_info']['max_carbs'][diet_type]
                st.write(f'Protein Requirement: {protein_req}g')
                st.write(f'Carbohydrate Limit: {carb_limit}g')

            # Sustainability Metrics
            st.subheader('Sustainability Metrics')
            co2_emissions = sum(data['sustainability_metrics']['co2_emissions_per_km'] * data['logistic_info']['market_distance_km'] * delivery_vars.get(f'Delivery[{i}]', 0) for i in range(data['planning_info']['horizon_days']))
            st.write(f'Total CO2 Emissions: {co2_emissions:.2f} kg')

            water_usage = sum(data['sustainability_metrics']['water_usage_per_kg'][item] * sum(purchase_df.loc[item]) for item in purchase_df.index)
            st.write(f'Total Water Usage: {water_usage:.2f} liters')

        elif model.status == GRB.INFEASIBLE:
            st.error('Model is infeasible')
        elif model.status == GRB.UNBOUNDED:
            st.error('Model is unbounded')
        else:
            st.warning(f'Optimization was stopped with status {model.status}')

if __name__ == '__main__':
    main()