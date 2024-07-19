import random
from typing import Dict, List, Tuple

class EnhancedAICompetitionSimulation:
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
        
        self.resources = {"OpenAI": 1000, "Google": 1000}
        self.reputation = {"OpenAI": 50, "Google": 50}
        self.market_share = {"OpenAI": 50, "Google": 50}
        
        self.payoff_matrix = self._initialize_payoff_matrix()
        self.action_costs = self._initialize_action_costs()
        
        self.wildcards = [
            "breakthrough_discovery",
            "major_ethics_scandal",
            "significant_talent_acquisition",
            "unexpected_partnership",
            "regulatory_crackdown"
        ]

    def _initialize_payoff_matrix(self):
        # Initialize with more realistic payoffs
        matrix = {}
        for state in self.S:
            for openai_action in self.A:
                for google_action in self.G:
                    openai_payoff = random.randint(60, 100)
                    google_payoff = random.randint(60, 100)
                    matrix[(state, openai_action, google_action)] = (openai_payoff, google_payoff)
        return matrix

    def _initialize_action_costs(self):
        return {
            "OpenAI": {action: random.randint(20, 50) for action in self.A},
            "Google": {action: random.randint(20, 50) for action in self.G}
        }

    def apply_wildcard(self):
        if random.random() < 0.1:  # 10% chance of a wildcard event
            event = random.choice(self.wildcards)
            if event == "breakthrough_discovery":
                lucky_company = random.choice(["OpenAI", "Google"])
                self.resources[lucky_company] += 200
                self.reputation[lucky_company] += 10
            elif event == "major_ethics_scandal":
                unlucky_company = random.choice(["OpenAI", "Google"])
                self.reputation[unlucky_company] -= 20
            elif event == "significant_talent_acquisition":
                lucky_company = random.choice(["OpenAI", "Google"])
                self.resources[lucky_company] += 100
                self.reputation[lucky_company] += 5
            elif event == "unexpected_partnership":
                self.market_share["OpenAI"] += 5
                self.market_share["Google"] += 5
            elif event == "regulatory_crackdown":
                self.resources["OpenAI"] -= 100
                self.resources["Google"] -= 100
            return event
        return None

    def state_transition(self, state: str, openai_action: str, google_action: str) -> str:
        # Enhanced state transition logic
        openai_strength = self.payoff_matrix[(state, openai_action, google_action)][0] + self.reputation["OpenAI"]
        google_strength = self.payoff_matrix[(state, openai_action, google_action)][1] + self.reputation["Google"]
        
        if openai_strength > google_strength + 20:
            return "openai_lead"
        elif google_strength > openai_strength + 20:
            return "google_lead"
        elif abs(openai_strength - google_strength) <= 20:
            return "neck_and_neck"
        elif random.random() < 0.1:  # 10% chance of disruption
            return "disrupted_by_new_entrant"
        elif self.reputation["OpenAI"] < 30 or self.reputation["Google"] < 30:
            return "ethical_concerns_dominate"
        else:
            return random.choice(self.S)

    def simulate_quarter(self, state: str) -> Dict[str, any]:
        openai_action = random.choice(self.A)
        google_action = random.choice(self.G)
        
        self.resources["OpenAI"] -= self.action_costs["OpenAI"][openai_action]
        self.resources["Google"] -= self.action_costs["Google"][google_action]
        
        openai_payoff, google_payoff = self.payoff_matrix[(state, openai_action, google_action)]
        
        self.market_share["OpenAI"] += (openai_payoff - google_payoff) // 10
        self.market_share["Google"] = 100 - self.market_share["OpenAI"]
        
        self.reputation["OpenAI"] += random.randint(-5, 5)
        self.reputation["Google"] += random.randint(-5, 5)
        
        next_state = self.state_transition(state, openai_action, google_action)
        wildcard_event = self.apply_wildcard()
        
        return {
            "initial_state": state,
            "openai_action": openai_action,
            "google_action": google_action,
            "resulting_state": next_state,
            "openai_payoff": openai_payoff,
            "google_payoff": google_payoff,
            "openai_resources": self.resources["OpenAI"],
            "google_resources": self.resources["Google"],
            "openai_reputation": self.reputation["OpenAI"],
            "google_reputation": self.reputation["Google"],
            "openai_market_share": self.market_share["OpenAI"],
            "google_market_share": self.market_share["Google"],
            "wildcard_event": wildcard_event
        }

    def run_simulation(self) -> List[Dict[str, any]]:
        results = []
        current_state = random.choice(self.S)
        for quarter in self.T:
            quarter_result = self.simulate_quarter(current_state)
            quarter_result["quarter"] = quarter
            results.append(quarter_result)
            current_state = quarter_result["resulting_state"]
        return results

# Run the simulation
sim = EnhancedAICompetitionSimulation()
simulation_results = sim.run_simulation()

# Print results
for result in simulation_results:
    print(f"Quarter: {result['quarter']}")
    print(f"Initial State: {result['initial_state']}")
    print(f"OpenAI Action: {result['openai_action']}")
    print(f"Google Action: {result['google_action']}")
    print(f"Resulting State: {result['resulting_state']}")
    print(f"OpenAI Payoff: {result['openai_payoff']}")
    print(f"Google Payoff: {result['google_payoff']}")
    print(f"OpenAI Resources: {result['openai_resources']}")
    print(f"Google Resources: {result['google_resources']}")
    print(f"OpenAI Reputation: {result['openai_reputation']}")
    print(f"Google Reputation: {result['google_reputation']}")
    print(f"OpenAI Market Share: {result['openai_market_share']}%")
    print(f"Google Market Share: {result['google_market_share']}%")
    if result['wildcard_event']:
        print(f"Wildcard Event: {result['wildcard_event']}")
    print("---")