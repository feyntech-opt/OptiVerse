import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import json

# Set up database connection
engine = create_engine('sqlite:///dolo_650_supply_chain.db')

# Function to load data
def load_data(table_name):
    return pd.read_sql_table(table_name, engine)

# Load data
production = load_data('production_solution')
sourcing = load_data('sourcing_solution')
distribution = load_data('distribution_solution')
facilities = load_data('facility')
post_offices = load_data('post_office')

# Dashboard title
st.title('Dolo 650 Supply Chain Optimization Dashboard')

# Key Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Production", f"{production['Value'].sum():,.0f} units")
col2.metric("Total Sourcing", f"{sourcing['Value'].sum():,.0f} units")
col3.metric("Total Distribution", f"{distribution['Value'].sum():,.0f} units")

# Production by Facility
st.subheader('Production by Facility')
prod_by_facility = production.groupby('FacilityID')['Value'].sum().reset_index()
prod_by_facility = prod_by_facility.merge(facilities[['FacilityID', 'Name']], on='FacilityID')
fig_prod = px.bar(prod_by_facility, x='Name', y='Value', title='Production by Facility')
st.plotly_chart(fig_prod)

# Sourcing Network
st.subheader('Sourcing Network')
fig_sourcing = go.Figure(data=[go.Sankey(
    node = dict(
      pad = 15,
      thickness = 20,
      line = dict(color = "black", width = 0.5),
      label = [f"Supplier {s}" for s in sourcing['SupplierID'].unique()] + 
              [f"Facility {f}" for f in sourcing['FacilityID'].unique()],
      color = "blue"
    ),
    link = dict(
      source = sourcing['SupplierID'].astype(int) - 1,  # Adjust for zero-indexing
      target = sourcing['FacilityID'].astype(int) - 1 + len(sourcing['SupplierID'].unique()),
      value = sourcing['Value']
  ))])
fig_sourcing.update_layout(title_text="Sourcing Network Flow", font_size=10)
st.plotly_chart(fig_sourcing)

# Distribution Choropleth Map
st.subheader('Distribution by State')
# Merge distribution data with post office data to get state information
distribution_with_state = distribution.merge(post_offices[['PostOfficeID', 'StateName']], on='PostOfficeID')
distribution_by_state = distribution_with_state.groupby('StateName')['Value'].sum().reset_index()

# Load India state geojson
with open('india_states.geojson', 'r') as f:
    india_states = json.load(f)

fig_map = px.choropleth_mapbox(distribution_by_state, 
                               geojson=india_states, 
                               locations='StateName', 
                               color='Value',
                               featureidkey="properties.ST_NM",  # This should match the state name field in your geojson
                               center={"lat": 20.5937, "lon": 78.9629},
                               mapbox_style="carto-positron", 
                               zoom=3,
                               color_continuous_scale="Viridis",
                               labels={'Value':'Distribution'})

fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig_map)

# Interesting Insights
st.subheader('Interesting Insights')
max_prod_facility = prod_by_facility.loc[prod_by_facility['Value'].idxmax(), 'Name']
st.write(f"- The facility with the highest production is {max_prod_facility}.")
st.write(f"- There are {len(distribution['PostOfficeID'].unique())} post offices receiving Dolo 650.")
st.write(f"- The supply chain involves {len(sourcing['SupplierID'].unique())} suppliers and {len(production['FacilityID'].unique())} production facilities.")
st.write(f"- The state with the highest distribution is {distribution_by_state.loc[distribution_by_state['Value'].idxmax(), 'StateName']}.")

# Add interactivity
if st.checkbox('Show Raw Data'):
    st.subheader('Raw Production Data')
    st.write(production)
    st.subheader('Raw Sourcing Data')
    st.write(sourcing)
    st.subheader('Raw Distribution Data')
    st.write(distribution)