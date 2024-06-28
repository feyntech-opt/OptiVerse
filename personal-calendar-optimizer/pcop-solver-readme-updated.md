# PCOP-Solver: Personal Calendar Optimization Problem Solver

## Table of Contents
1. [Introduction](#introduction)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Input Data Format](#input-data-format)
6. [Solver Options](#solver-options)
7. [Output](#output)
8. [Mathematical Model](#mathematical-model)
9. [Customization](#customization)
10. [Contributing](#contributing)
11. [License](#license)

## Introduction

PCOP-Solver is a Python-based tool designed to solve the Personal Calendar Optimization Problem (PCOP). It helps individuals optimize their daily schedules and long-term plans over a 6-month period, balancing various activities, personal goals, and constraints to maximize productivity and well-being.

## Features

- Optimize personal schedules over a 6-month horizon
- Balance daily activities with long-term goals
- Consider multiple objectives: productivity, well-being, and goal progress
- Handle various constraints: time windows, precedence, breaks, and more
- Interactive Streamlit-based user interface for easy use
- Visualize results with tables and Gantt charts
- Flexible JSON-based input for easy customization

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/your-username/PCOP-Solver.git
   cd PCOP-Solver
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Prepare your input data in JSON format (see [Input Data Format](#input-data-format) section).

2. Run the Streamlit app:
   ```
   streamlit run pcop_streamlit_app.py
   ```

3. Upload your JSON file through the web interface.

4. Adjust solver options if needed and click "Run Optimization" to see the results.

Alternatively, you can use the solver directly in Python:

```python
from pcop_solver import load_pcop_data, create_pcop_model, solve_pcop_model

pcop_data = load_pcop_data('your_pcop_data.json')
model, activity_intervals, num_days = create_pcop_model(pcop_data)
schedule = solve_pcop_model(model, activity_intervals, num_days, pcop_data['solver_options'])
```

## Input Data Format

The input data should be in JSON format, containing both the PCOP data and solver options. Here's an example structure:

```json
{
  "pcop_data": {
    "timeHorizon": {
      "startDate": "2024-07-01",
      "endDate": "2024-12-31",
      "intervalMinutes": 30
    },
    "activities": [
      {
        "name": "Sleep",
        "dailyMinDuration": 420,
        "dailyMaxDuration": 540,
        "preferredStartTime": "22:00",
        "preferredEndTime": "07:00"
      },
      // ... other activities
    ],
    "goals": [
      {
        "name": "Japanese Proficiency",
        "targetLevel": "N4",
        "milestones": [
          {
            "description": "Complete Genki I textbook",
            "dueDate": "2024-09-30"
          },
          // ... other milestones
        ]
      },
      // ... other goals
    ],
    "constraints": {
      "precedence": [
        {
          "activity": "Exercise",
          "notAfter": "Eating",
          "minGapMinutes": 60
        },
        // ... other precedence constraints
      ],
      "breaks": {
        "activity": "Work",
        "breakDurationMinutes": 15,
        "afterDurationMinutes": 120
      },
      "flexibility": {
        "weekendDifferentiation": true,
        "holidays": ["2024-12-25", "2024-12-31"]
      }
    },
    "objectiveWeights": {
      "dailyProductivity": 0.3,
      "dailyWellbeing": 0.3,
      "goalProgress": 0.4
    }
  },
  "solver_options": {
    "time_limit_seconds": 300,
    "solution_limit": 1,
    "log_search_progress": true
  }
}
```

## Solver Options

- `time_limit_seconds`: Maximum time (in seconds) the solver will run
- `solution_limit`: Maximum number of solutions to find before stopping
- `log_search_progress`: Whether to log the search progress

These options can be adjusted in the JSON input file or through the Streamlit interface.

## Output

The solver produces an optimized schedule, which includes:

1. A day-by-day breakdown of activities
2. A Gantt chart visualization of the schedule
3. A list of goals and milestones
4. A downloadable CSV file of the full schedule

## Mathematical Model

The PCOP can be formulated as a constraint programming model. Here's the algebraic formulation:

### Sets and Indices

- T: Set of time slots (e.g., 30-minute intervals over 6 months)
- D: Set of days in the planning horizon
- A: Set of activities
- G: Set of goals
- M: Set of milestones

### Decision Variables

- x[a,t] ∈ {0,1}: Binary variable, 1 if activity a starts at time slot t, 0 otherwise
- y[a,d] ∈ ℤ⁺: Integer variable, duration of activity a on day d
- z[g] ∈ [0,1]: Continuous variable, progress towards goal g

### Objective Function

Maximize: 
```
∑(a∈A, d∈D) (w_prod * y[a,d] * prod[a] + w_well * y[a,d] * well[a]) + w_goal * ∑(g∈G) z[g]
```

Where:
- w_prod, w_well, w_goal: Weights for productivity, well-being, and goal progress
- prod[a], well[a]: Productivity and well-being factors for activity a

### Constraints

1. Activity duration limits:
   ```
   min_dur[a] ≤ y[a,d] ≤ max_dur[a], ∀a∈A, d∈D
   ```

2. No overlap of activities:
   ```
   ∑(a∈A) x[a,t] ≤ 1, ∀t∈T
   ```

3. Continuity of activities:
   ```
   x[a,t] = 1 ⇒ x[a,t+k] = 0, ∀a∈A, t∈T, k∈{1,...,y[a,d]-1}
   ```

4. Precedence constraints:
   ```
   end_time[a1,d] + min_gap ≤ start_time[a2,d], ∀(a1,a2)∈Precedence, d∈D
   ```

5. Time window constraints:
   ```
   start_time[a,d] ∈ time_window[a], ∀a∈A, d∈D
   ```

6. Goal progress constraints:
   ```
   z[g] = f(∑(d∈D, a∈A_g) y[a,d]), ∀g∈G
   ```
   Where A_g is the set of activities contributing to goal g, and f is a function mapping activity durations to goal progress.

7. Milestone constraints:
   ```
   z[g] ≥ progress_required[m], ∀m∈M, g=goal[m], d≥due_date[m]
   ```

This model captures the essence of the PCOP, balancing daily activities with long-term goals while respecting various constraints. The actual implementation may include additional constraints and variables to handle specific requirements.

## Customization

You can customize the PCOP-Solver by modifying the following files:

- `pcop_solver.py`: Core optimization logic
- `pcop_streamlit_app.py`: User interface
- Input JSON file: Problem-specific data and constraints

## Contributing

Contributions to PCOP-Solver are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
