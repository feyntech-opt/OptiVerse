import streamlit as st
import json
from datetime import datetime, timedelta
import pandas as pd
import plotly.figure_factory as ff

# Import functions from your updated pcop_solver.py
from . import create_pcop_model, solve_pcop_model

# Convert schedule to DataFrame for easy display
def schedule_to_df(schedule, start_date):
    df_data = []
    for day, day_schedule in enumerate(schedule):
        date = start_date + timedelta(days=day)
        for activity, start, duration in day_schedule:
            start_time = date + timedelta(minutes=start)
            end_time = start_time + timedelta(minutes=duration)
            df_data.append({
                'Task': activity,
                'Start': start_time,
                'Finish': end_time,
                'Resource': f'Day {day + 1}'
            })
    return pd.DataFrame(df_data)

# Create Gantt chart
def create_gantt_chart(df):
    fig = ff.create_gantt(df, index_col='Resource', show_colorbar=True, group_tasks=True)
    fig.update_layout(autosize=False, width=800, height=600, title='PCOP Schedule Gantt Chart')
    return fig

# Streamlit app
def main():
    st.title('Personal Calendar Optimization Problem (PCOP) Solver')

    uploaded_file = st.file_uploader("Choose a PCOP JSON file", type="json")
    if uploaded_file is not None:
        pcop_data = json.load(uploaded_file)
        st.success("PCOP data loaded successfully!")

        # Display solver options
        st.subheader("Solver Options")
        time_limit = st.number_input("Time Limit (seconds)", 
                                     value=pcop_data['solver_options']['time_limit_seconds'],
                                     min_value=1, max_value=3600)
        solution_limit = st.number_input("Solution Limit", 
                                         value=pcop_data['solver_options']['solution_limit'],
                                         min_value=1, max_value=100)
        log_search = st.checkbox("Log Search Progress", 
                                 value=pcop_data['solver_options']['log_search_progress'])

        # Update solver options in pcop_data
        pcop_data['solver_options']['time_limit_seconds'] = time_limit
        pcop_data['solver_options']['solution_limit'] = solution_limit
        pcop_data['solver_options']['log_search_progress'] = log_search

        if st.button('Run Optimization'):
            with st.spinner('Optimizing schedule...'):
                model, activity_intervals, num_days = create_pcop_model(pcop_data)
                schedule = solve_pcop_model(model, activity_intervals, num_days, pcop_data['solver_options'])

            if schedule:
                st.success("Optimization complete!")
                start_date = datetime.strptime(pcop_data['pcop_data']['timeHorizon']['startDate'], '%Y-%m-%d')
                
                # Display schedule as a table
                st.subheader("Optimized Schedule (First 7 Days)")
                df = schedule_to_df(schedule[:7], start_date)
                st.dataframe(df)

                # Display Gantt chart
                st.subheader("Schedule Gantt Chart")
                fig = create_gantt_chart(df)
                st.plotly_chart(fig)

                # Display goals and milestones
                st.subheader("Goals and Milestones")
                for goal in pcop_data['pcop_data']['goals']:
                    st.write(f"**{goal['name']}**: {goal.get('targetDescription', goal.get('targetLevel', 'N/A'))}")
                    for milestone in goal['milestones']:
                        st.write(f"- {milestone['description']} (Due: {milestone['dueDate']})")

                # Download link for full schedule
                full_df = schedule_to_df(schedule, start_date)
                csv = full_df.to_csv(index=False)
                st.download_button(
                    label="Download full schedule as CSV",
                    data=csv,
                    file_name="pcop_schedule.csv",
                    mime="text/csv",
                )
            else:
                st.error("No feasible solution found. Please check your constraints and try again.")

if __name__ == "__main__":
    main()
