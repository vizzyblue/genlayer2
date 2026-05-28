# CONTRACT 15 — AI-Judged Bounty Board
# Use-case: A bounty poster describes success criteria in plain English;
# hunters submit solutions; LLM judges if the bounty conditions are met.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
 
class BountyBoard(gl.Contract):
    bounty_description: str
    success_criteria: str
    reward: gl.u256
    poster: gl.Address
    claimed: bool
    winner: str
    submissions: TreeMap[str, str]
 
    def __init__(self, bounty_description: str, success_criteria: str, reward: int):
        self.bounty_description = bounty_description
        self.success_criteria = success_criteria
        self.reward = gl.u256(reward)
        self.poster = gl.message.sender
        self.claimed = False
        self.winner = ""
 
    @gl.public.write
    def submit_solution(self, solution_url: str, solution_description: str) -> dict:
        """
        Hunter submits a solution; LLM judges if it meets the bounty criteria.
        """
        assert not self.claimed, "Bounty already claimed"
        hunter = str(gl.message.sender)
 
        def nondet() -> str:
            web_content = ""
            try:
                response = gl.nondet.web.get(solution_url)
                web_content = response.body.decode("utf-8")[:2000]
            except Exception:
                web_content = "(URL not accessible)"
 
            prompt = (
                f"Bounty: {self.bounty_description}\n"
                f"Success Criteria: {self.success_criteria}\n\n"
                f"Submitted solution description: {solution_description}\n"
                f"Solution URL content preview: {web_content}\n\n"
                "Does this submission meet the bounty success criteria?\n"
                'Respond ONLY with JSON:\n'
                '{"criteria_met": true|false, "score": int(0-100), '
                '"met_criteria": [str], "unmet_criteria": [str], "verdict": str}\n'
                "No markdown."
            )
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
        result["hunter"] = hunter
        result["url"] = solution_url
 
        if result["criteria_met"] and not self.claimed:
            self.claimed = True
            self.winner = hunter
 
        self.submissions[hunter] = json.dumps(result)
        return result
 
    @gl.public.view
    def get_status(self) -> dict:
        return {
            "claimed": self.claimed,
            "winner": self.winner,
            "reward": int(self.reward),
            "bounty": self.bounty_description,
        }
 
