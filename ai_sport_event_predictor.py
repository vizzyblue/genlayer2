# CONTRACT 11 — AI Sports Event Predictor
# Use-case: Fetches live sports standings from the web and uses LLM to
# predict match outcomes with confidence scores.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
 
class SportsPredictionMarket(gl.Contract):
    sport: str
    predictions: TreeMap[str, str]
    resolved: TreeMap[str, bool]
 
    def __init__(self, sport: str):
        self.sport = sport
 
    @gl.public.write
    def predict_match(self, team1: str, team2: str, stats_url: str) -> dict:
        """
        Fetches live team stats and predicts match outcome with LLM reasoning.
        """
        match_id = f"{team1}_vs_{team2}".lower().replace(" ", "_")
 
        def nondet() -> str:
            response = gl.nondet.web.get(stats_url)
            stats_data = response.body.decode("utf-8")[:3000]
 
            prompt = (
                f"Sport: {self.sport}\n"
                f"Match: {team1} vs {team2}\n\n"
                f"Live Stats/Standings Data:\n{stats_data}\n\n"
                "Analyze the data and predict the match outcome.\n"
                'Respond ONLY with JSON:\n'
                '{"winner": str, "confidence": int(0-100), '
                '"team1_win_prob": int, "draw_prob": int, "team2_win_prob": int, '
                '"reasoning": str, "key_factors": [str]}\n'
                "No markdown."
            )
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
        result["match_id"] = match_id
        self.predictions[match_id] = json.dumps(result)
        return result
 
    @gl.public.view
    def get_prediction(self, match_id: str) -> dict:
        if match_id not in self.predictions:
            return {}
        return json.loads(self.predictions[match_id])
 
