from strategy import EnhancedAICompetitionSimulation
from collections import Counter


def analyze_successful_strategies(num_simulations=1000):
    successful_strategies = []
    for _ in range(num_simulations):
        print(f"Running simulation {_}")
        sim = EnhancedAICompetitionSimulation()
        results = sim.run_simulation()
        final_result = results[-1]
        
        # Define success criteria (e.g., market share > 60%)
        if final_result['openai_market_share'] > 60:
            successful_strategies.extend([(result['quarter'], result['openai_action']) for result in results])
        elif final_result['google_market_share'] > 60:
            successful_strategies.extend([(result['quarter'], result['google_action']) for result in results])

    # Count the frequency of each action in successful strategies
    strategy_counts = Counter(successful_strategies)
    return strategy_counts.most_common(10)

# Analyze successful strategies
top_strategies = analyze_successful_strategies()

print("Top 10 Most Successful Strategies:")
for (quarter, action), count in top_strategies:
    print(f"{quarter} - {action}: {count} occurrences")