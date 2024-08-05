import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from data_loader import load_data
from model import create_model
from optimizer import optimize_model
import config

def run_app():
    st.set_page_config(page_title="EnergySage: India's Power Transition Planner", layout="wide")

    st.title("EnergySage: India's Power Transition Planner")
    st.write("Optimize India's energy transition strategy from 2024 to 2030")

    # User inputs in the main screen
    st.header("Model Parameters")
    
    col1, col2 = st.columns(2)
    with col1:
        config.START_YEAR = st.number_input("Start Year", min_value=2024, max_value=2030, value=config.START_YEAR)
        config.END_YEAR = st.number_input("End Year", min_value=config.START_YEAR, max_value=2050, value=config.END_YEAR)
        config.TOTAL_BUDGET = st.number_input("Total Budget (lakh crore ₹)", min_value=30.0, max_value=200.0, value=float(config.TOTAL_BUDGET/1e11), step=0.1) * 1e11
        config.YEARLY_BUDGET_FRACTION = st.slider("Yearly Budget Fraction", 0.1, 0.5, float(config.YEARLY_BUDGET_FRACTION), 0.01)
        config.MIN_TOTAL_CAPACITY = st.number_input("Minimum Total Capacity (MW)", min_value=500000, max_value=1000000, value=config.MIN_TOTAL_CAPACITY)
        config.MAX_TOTAL_CAPACITY = st.number_input("Maximum Total Capacity (MW)", min_value=config.MIN_TOTAL_CAPACITY, max_value=1500000, value=config.MAX_TOTAL_CAPACITY)
        config.RENEWABLE_TARGET = st.slider("Renewable Energy Target (%)", 30.0, 70.0, float(config.RENEWABLE_TARGET*100), 0.1) / 100

    with col2:
        config.EMISSIONS_INCREASE_LIMIT = st.slider("Emissions Increase Limit (%)", -20.0, 20.0, float(config.EMISSIONS_INCREASE_LIMIT*100), 0.1) / 100
        config.MIN_SOURCES_USED = st.number_input("Minimum Sources Used", min_value=1, max_value=10, value=config.MIN_SOURCES_USED)
        config.TOTAL_CAPACITY_PENALTY = st.number_input("Total Capacity Penalty", min_value=1e8, max_value=1e12, value=float(config.TOTAL_CAPACITY_PENALTY), format="%.2e")
        config.CAPACITY_PENALTY = st.number_input("Capacity Penalty", min_value=1e4, max_value=1e8, value=float(config.CAPACITY_PENALTY), format="%.2e")
        config.DIVERSITY_INCENTIVE = st.number_input("Diversity Incentive", min_value=1e5, max_value=1e9, value=float(config.DIVERSITY_INCENTIVE), format="%.2e")
        config.PRODUCTION_WEIGHT = st.number_input("Production Weight", min_value=1e-4, max_value=1e-1, value=float(config.PRODUCTION_WEIGHT), format="%.2e")
        config.TIME_LIMIT = st.number_input("Solver Time Limit (seconds)", min_value=60, max_value=7200, value=config.TIME_LIMIT)
        config.MIP_GAP = st.slider("MIP Gap", 0.001, 0.1, float(config.MIP_GAP), 0.001)

    # Load data
    data = load_data()

    # Run optimization
    if st.button("Run Optimization"):
        with st.spinner("Optimizing energy transition strategy..."):
            model, investment, capacity_slack, total_capacity_var, total_capacity_slack, source_used, total_production = create_model(data)
            results = optimize_model(model, data, investment, capacity_slack, total_capacity_var, total_capacity_slack, source_used, total_production)

        if results:
            display_results(results, data)
        else:
            st.error("No optimal solution found. Try adjusting the parameters.")

def display_results(results, data):
    st.header("Optimization Results")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Investment", f"₹{results['total_investment'] / 1e11:.2f} lakh crore")
    col2.metric("Total Capacity", f"{results['total_capacity']:.2f} MW")
    col3.metric("Annual Production", f"{results['total_production']:.2f} TWh")

    col1, col2, col3 = st.columns(3)
    col1.metric("Renewable Capacity", f"{results['renewable_capacity']:.2f} MW")
    col2.metric("Renewable Percentage", f"{results['renewable_capacity']/results['total_capacity']*100:.2f}%")
    col3.metric("Emissions Change", f"{results['emissions_change']:.2f}%")

    st.subheader("Investment Distribution")
    fig_investment = px.pie(
        values=[data['total_investment'] for data in results['source_investments'].values()],
        names=list(results['source_investments'].keys()),
        title="Investment Distribution by Energy Source"
    )
    st.plotly_chart(fig_investment)

    st.subheader("Capacity Addition")
    fig_capacity = px.bar(
        x=list(results['source_investments'].keys()),
        y=[data['capacity_addition'] for data in results['source_investments'].values()],
        title="Capacity Addition by Energy Source"
    )
    fig_capacity.update_layout(xaxis_title="Energy Source", yaxis_title="Capacity Addition (MW)")
    st.plotly_chart(fig_capacity)

    st.subheader("Yearly Investment Plan")
    yearly_data = []
    for source, data in results['source_investments'].items():
        for year, investment in data['yearly_investments'].items():
            yearly_data.append({'Source': source, 'Year': year, 'Investment': investment / 1e11})
    df_yearly = pd.DataFrame(yearly_data)
    fig_yearly = px.bar(
        df_yearly,
        x='Year',
        y='Investment',
        color='Source',
        title="Yearly Investment Plan",
        labels={'Investment': 'Investment (lakh crore ₹)'}
    )
    st.plotly_chart(fig_yearly)

    st.subheader("Detailed Results by Energy Source")
    for source, data in results['source_investments'].items():
        with st.expander(f"{source} Details"):
            col1, col2 = st.columns(2)
            col1.metric("Total Investment", f"₹{data['total_investment'] / 1e11:.2f} lakh crore")
            col2.metric("Capacity Addition", f"{data['capacity_addition']:.2f} MW")
            col1.metric("Final Capacity", f"{data['final_capacity']:.2f} MW")
            col2.metric("Annual Production", f"{data['annual_production']:.2f} TWh")
            col1.metric("Capacity Factor", f"{data['capacity_factor']:.2f}")
            if data['capacity_shortfall'] > 0:
                col2.metric("Capacity Shortfall", f"{data['capacity_shortfall']:.2f} MW")

    st.subheader("Model Parameters Used")
    st.write(f"Start Year: {config.START_YEAR}")
    st.write(f"End Year: {config.END_YEAR}")
    st.write(f"Total Budget: ₹{config.TOTAL_BUDGET / 1e11:.2f} lakh crore")
    st.write(f"Yearly Budget Fraction: {config.YEARLY_BUDGET_FRACTION:.2f}")
    st.write(f"Minimum Total Capacity: {config.MIN_TOTAL_CAPACITY} MW")
    st.write(f"Maximum Total Capacity: {config.MAX_TOTAL_CAPACITY} MW")
    st.write(f"Renewable Energy Target: {config.RENEWABLE_TARGET * 100:.2f}%")
    st.write(f"Emissions Increase Limit: {config.EMISSIONS_INCREASE_LIMIT * 100:.2f}%")
    st.write(f"Minimum Sources Used: {config.MIN_SOURCES_USED}")
    st.write(f"Total Capacity Penalty: {config.TOTAL_CAPACITY_PENALTY:.2e}")
    st.write(f"Capacity Penalty: {config.CAPACITY_PENALTY:.2e}")
    st.write(f"Diversity Incentive: {config.DIVERSITY_INCENTIVE:.2e}")
    st.write(f"Production Weight: {config.PRODUCTION_WEIGHT:.2e}")
    st.write(f"Solver Time Limit: {config.TIME_LIMIT} seconds")
    st.write(f"MIP Gap: {config.MIP_GAP:.4f}")

if __name__ == "__main__":
    run_app()