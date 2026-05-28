# CONTRACT 18 — Social Media Trend Oracle
# Use-case: Fetches trending topics from a public source and uses LLM to
# summarize, categorize, and assess market/investment relevance.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
 
class TrendOracle(gl.Contract):
    category: str
    trend_history: DynArray[str]
    update_count: gl.u256
 
    def __init__(self, category: str):
        self.category = category
        self.update_count = gl.u256(0)
 
    @gl.public.write
    def fetch_trends(self, source_url: str) -> dict:
        """
        Fetches a trends page and uses LLM to extract and categorize trending topics.
        """
        self.update_count = gl.u256(int(self.update_count) + 1)
 
        def nondet() -> str:
            response = gl.nondet.web.get(source_url)
            content = response.body.decode("utf-8")[:3000]
 
            prompt = (
                f"Category focus: {self.category}\n\n"
                f"Web content:\n{content}\n\n"
                "Extract the top trending topics from this page relevant to the category.\n"
                "Assess each trend's momentum (rising/stable/falling) and relevance.\n"
                'Respond ONLY with JSON:\n'
                '{"trends": [{"topic": str, "momentum": str, "relevance_score": int, "summary": str}], '
                '"top_trend": str, "category_sentiment": "bullish"|"bearish"|"neutral"}\n'
                "No markdown."
            )
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
        self.trend_history.append(json.dumps(result))
        return result
 
    @gl.public.view
    def get_latest_trends(self) -> dict:
        if not self.trend_history:
            return {}
        return json.loads(self.trend_history[-1])
 
 
