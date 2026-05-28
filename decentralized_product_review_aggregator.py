# CONTRACT 12 — Decentralized Product Review Aggregator
# Use-case: Collects reviews, uses LLM to detect fake/bot reviews and
# computes a trust-weighted aggregate rating.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
 
class TrustWeightedReviews(gl.Contract):
    product: str
    reviews: DynArray[str]
    total_trust_score: gl.u256
    total_weight: gl.u256
    flagged_reviews: DynArray[str]
 
    def __init__(self, product: str):
        self.product = product
        self.total_trust_score = gl.u256(0)
        self.total_weight = gl.u256(0)
 
    @gl.public.write
    def submit_review(self, rating: int, review_text: str) -> dict:
        """
        Submits a review; LLM detects if it's genuine and assigns trust weight.
        """
        assert 1 <= rating <= 5, "Rating must be 1-5"
        reviewer = str(gl.message.sender)
 
        prompt = (
            f"Product: {self.product}\n"
            f"Rating: {rating}/5\n"
            f'Review: "{review_text}"\n\n'
            "Detect if this is a fake, bot-generated, or incentivized review.\n"
            "Assign authenticity weight 0-10 (10 = very authentic, 0 = clearly fake).\n"
            'Respond ONLY with JSON:\n'
            '{"authentic": true|false, "trust_weight": int(0-10), '
            '"flags": [str], "verdict": str}\n'
            "No markdown."
        )
 
        def nondet() -> str:
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
 
        review_entry = json.dumps({
            "reviewer": reviewer, "rating": rating,
            "text": review_text, **result
        })
 
        if result["authentic"]:
            self.reviews.append(review_entry)
            weight = result["trust_weight"]
            self.total_trust_score = gl.u256(int(self.total_trust_score) + rating * weight)
            self.total_weight = gl.u256(int(self.total_weight) + weight)
        else:
            self.flagged_reviews.append(review_entry)
 
        return result
 
    @gl.public.view
    def weighted_rating(self) -> float:
        if int(self.total_weight) == 0:
            return 0.0
        return int(self.total_trust_score) / int(self.total_weight)
 
    @gl.public.view
    def review_count(self) -> dict:
        return {"authentic": len(self.reviews), "flagged": len(self.flagged_reviews)}
 
