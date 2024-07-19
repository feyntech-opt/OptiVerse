from strategy import EnhancedAICompetitionSimulation
import matplotlib.pyplot as plt
from typing import List, Dict

def get_most_interesting_simulation(num_simulations=100) -> List[Dict]:
    interesting_outcomes = []
    for _ in range(num_simulations):
        sim = EnhancedAICompetitionSimulation()
        results = sim.run_simulation()
        final_result = results[-1]
        
        # Define criteria for interesting outcomes
        if (abs(final_result['openai_market_share'] - final_result['google_market_share']) > 20 or
            final_result['resulting_state'] == 'disrupted_by_new_entrant' or
            any(result['wildcard_event'] for result in results)):
            interesting_outcomes.append(results)
    
    # Select the most interesting outcome
    if interesting_outcomes:
        return max(interesting_outcomes, key=lambda x: abs(x[-1]['openai_market_share'] - x[-1]['google_market_share']))
    else:
        return []  # Return an empty list if no interesting outcomes found

def create_visualizations(simulation_results: List[Dict]):
    if not simulation_results:
        print("No interesting simulation results to visualize.")
        return

    quarters = [result['quarter'] for result in simulation_results]
    openai_market_share = [result['openai_market_share'] for result in simulation_results]
    google_market_share = [result['google_market_share'] for result in simulation_results]
    openai_resources = [result['openai_resources'] for result in simulation_results]
    google_resources = [result['google_resources'] for result in simulation_results]
    openai_reputation = [result['openai_reputation'] for result in simulation_results]
    google_reputation = [result['google_reputation'] for result in simulation_results]

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 15))

    # Market Share
    ax1.plot(quarters, openai_market_share, label='OpenAI', marker='o')
    ax1.plot(quarters, google_market_share, label='Google', marker='s')
    ax1.set_ylabel('Market Share (%)')
    ax1.set_title('Market Share Over Time')
    ax1.legend()

    # Resources
    ax2.plot(quarters, openai_resources, label='OpenAI', marker='o')
    ax2.plot(quarters, google_resources, label='Google', marker='s')
    ax2.set_ylabel('Resources')
    ax2.set_title('Resource Changes Over Time')
    ax2.legend()

    # Reputation
    ax3.plot(quarters, openai_reputation, label='OpenAI', marker='o')
    ax3.plot(quarters, google_reputation, label='Google', marker='s')
    ax3.set_ylabel('Reputation')
    ax3.set_title('Reputation Changes Over Time')
    ax3.legend()

    plt.tight_layout()
    plt.show()

# Usage
most_interesting_simulation = get_most_interesting_simulation()
create_visualizations(most_interesting_simulation)