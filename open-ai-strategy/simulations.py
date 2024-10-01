from strategy import EnhancedAICompetitionSimulation
import random
from typing import List, Dict

# If you need to use Counter for any additional analysis
from collections import Counter

import random
from collections import Counter

def run_multiple_simulations(num_simulations=100):
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
        return None

# Run multiple simulations and get the most interesting outcome
most_interesting_simulation = run_multiple_simulations()

if most_interesting_simulation:
    print("Most Interesting Simulation Outcome:")
    for result in most_interesting_simulation:
        print(f"Quarter: {result['quarter']}")
        print(f"Resulting State: {result['resulting_state']}")
        print(f"OpenAI Market Share: {result['openai_market_share']}%")
        print(f"Google Market Share: {result['google_market_share']}%")
        if result['wildcard_event']:
            print(f"Wildcard Event: {result['wildcard_event']}")
        print("---")
else:
    print("No interesting outcomes found in the simulations.")