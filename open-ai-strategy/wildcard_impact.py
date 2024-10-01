from strategy import EnhancedAICompetitionSimulation
from typing import Dict

def analyze_wildcard_impact(num_simulations=1000):
    sim = EnhancedAICompetitionSimulation()  # Create an instance to access wildcards
    wildcard_impacts = {event: {'count': 0, 'avg_market_shift': 0} for event in sim.wildcards}
    
    for _ in range(num_simulations):
        sim = EnhancedAICompetitionSimulation()
        results = sim.run_simulation()
        
        for i, result in enumerate(results):
            if result['wildcard_event']:
                event = result['wildcard_event']
                wildcard_impacts[event]['count'] += 1
                
                if i > 0:
                    market_shift = abs(result['openai_market_share'] - results[i-1]['openai_market_share'])
                    wildcard_impacts[event]['avg_market_shift'] += market_shift

    # Calculate average market shift for each wildcard event
    for event in wildcard_impacts:
        if wildcard_impacts[event]['count'] > 0:
            wildcard_impacts[event]['avg_market_shift'] /= wildcard_impacts[event]['count']

    return wildcard_impacts

# Analyze wildcard event impacts
wildcard_impacts = analyze_wildcard_impact()

print("Wildcard Event Impacts:")
for event, impact in wildcard_impacts.items():
    if impact['count'] > 0:
        print(f"{event}:")
        print(f"  Occurrences: {impact['count']}")
        print(f"  Average Market Share Shift: {impact['avg_market_shift']:.2f}%")
        print()