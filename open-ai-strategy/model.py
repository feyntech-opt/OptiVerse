import itertools
from typing import Dict, List, Tuple
import numpy as np

class AICompetitionSimulation:
    def __init__(self):
        self.T = ["2024Q3", "2024Q4", "2025Q1", "2025Q2"]
        
        self.A = [
            "launch_gpt4o_mini",
            "enhance_gpt4_turbo_vision",
            "improve_dalle3",
            "develop_strawberry_project",
            "launch_ai_search_engine"
        ]
        
        self.G = [
            "upgrade_gemini_15",
            "develop_project_astra",
            "launch_gemini_live",
            "improve_trillium_tpus",
            "enhance_ai_search"
        ]
        
        self.S = [
            "openai_lead",
            "google_lead",
            "neck_and_neck",
            "disrupted_by_new_entrant",
            "ethical_concerns_dominate"
        ]
        
        self.payoff_matrix = self._initialize_payoff_matrix()

    def _initialize_payoff_matrix(self) -> Dict[Tuple[str, str, str], Tuple[int, int]]:
        matrix = {}
        for state in self.S:
            for openai_action in self.A:
                for google_action in self.G:
                    # Initialize with random payoffs for demonstration
                    # In a real scenario, these would be carefully calculated
                    openai_payoff = np.random.randint(50, 100)
                    google_payoff = np.random.randint(50, 100)
                    matrix[(state, openai_action, google_action)] = (openai_payoff, google_payoff)
        return matrix

    def state_transition(self, state: str, openai_action: str, google_action: str) -> str:
        # Simplified state transition logic
        if openai_action == "launch_ai_search_engine" and google_action != "enhance_ai_search":
            return "openai_lead"
        elif google_action == "develop_project_astra" and openai_action != "develop_strawberry_project":
            return "google_lead"
        elif openai_action == "launch_gpt4o_mini" and google_action == "upgrade_gemini_15":
            return "neck_and_neck"
        elif (openai_action == "enhance_gpt4_turbo_vision" or google_action == "launch_gemini_live"):
            return "disrupted_by_new_entrant"
        else:
            return "ethical_concerns_dominate"

    def simulate_all_scenarios(self) -> List[Dict[str, any]]:
        scenarios = []
        for quarter, state, openai_action, google_action in itertools.product(self.T, self.S, self.A, self.G):
            next_state = self.state_transition(state, openai_action, google_action)
            openai_payoff, google_payoff = self.payoff_matrix[(state, openai_action, google_action)]
            
            scenarios.append({
                "quarter": quarter,
                "initial_state": state,
                "openai_action": openai_action,
                "google_action": google_action,
                "resulting_state": next_state,
                "openai_payoff": openai_payoff,
                "google_payoff": google_payoff
            })
        
        return scenarios

    def analyze_results(self, scenarios: List[Dict[str, any]]) -> Dict[str, any]:
        total_scenarios = len(scenarios)
        openai_wins = sum(1 for s in scenarios if s['openai_payoff'] > s['google_payoff'])
        google_wins = sum(1 for s in scenarios if s['google_payoff'] > s['openai_payoff'])
        ties = total_scenarios - openai_wins - google_wins
        
        avg_openai_payoff = sum(s['openai_payoff'] for s in scenarios) / total_scenarios
        avg_google_payoff = sum(s['google_payoff'] for s in scenarios) / total_scenarios
        
        most_common_state = max(set(s['resulting_state'] for s in scenarios), 
                                key=lambda x: sum(1 for s in scenarios if s['resulting_state'] == x))
        
        return {
            "total_scenarios": total_scenarios,
            "openai_wins": openai_wins,
            "google_wins": google_wins,
            "ties": ties,
            "avg_openai_payoff": avg_openai_payoff,
            "avg_google_payoff": avg_google_payoff,
            "most_common_resulting_state": most_common_state
        }

# Run the simulation
sim = AICompetitionSimulation()
all_scenarios = sim.simulate_all_scenarios()
analysis = sim.analyze_results(all_scenarios)

# Print analysis
print("Simulation Analysis:")
for key, value in analysis.items():
    print(f"{key}: {value}")

# Print a few sample scenarios
print("\nSample Scenarios:")
for scenario in all_scenarios[:5]:  # Print first 5 scenarios
    print(f"Quarter: {scenario['quarter']}")
    print(f"Initial State: {scenario['initial_state']}")
    print(f"OpenAI Action: {scenario['openai_action']}")
    print(f"Google Action: {scenario['google_action']}")
    print(f"Resulting State: {scenario['resulting_state']}")
    print(f"OpenAI Payoff: {scenario['openai_payoff']}")
    print(f"Google Payoff: {scenario['google_payoff']}")
    print("---")