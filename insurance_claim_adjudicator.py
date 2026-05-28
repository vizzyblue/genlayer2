# CONTRACT 16 — Insurance Claim Adjudicator
# Use-case: Policyholders submit claims with evidence URLs; LLM adjudicates
# based on policy terms and evidence quality.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
 
class InsuranceClaimAdjudicator(gl.Contract):
    policy_terms: str
    insurer: gl.Address
    claims: TreeMap[str, str]
    total_claims: gl.u256
    total_approved: gl.u256
 
    def __init__(self, policy_terms: str):
        self.policy_terms = policy_terms
        self.insurer = gl.message.sender
        self.total_claims = gl.u256(0)
        self.total_approved = gl.u256(0)
 
    @gl.public.write
    def file_claim(self, claim_description: str, evidence_url: str, amount: int) -> dict:
        """
        Files a claim; LLM adjudicates based on policy terms and evidence.
        """
        claimant = str(gl.message.sender)
        self.total_claims = gl.u256(int(self.total_claims) + 1)
        claim_id = f"claim_{int(self.total_claims)}"
 
        def nondet() -> str:
            evidence_content = ""
            try:
                response = gl.nondet.web.get(evidence_url)
                evidence_content = response.body.decode("utf-8")[:2000]
            except Exception:
                evidence_content = "(Evidence URL not accessible)"
 
            prompt = (
                f"Insurance Policy Terms:\n{self.policy_terms}\n\n"
                f"Claim Description: {claim_description}\n"
                f"Claimed Amount: {amount} tokens\n"
                f"Evidence Content: {evidence_content}\n\n"
                "Adjudicate this claim based on policy terms and evidence provided.\n"
                'Respond ONLY with JSON:\n'
                '{"decision": "approved"|"partial"|"denied", '
                '"approved_amount": int, "coverage_ratio": float, '
                '"reasoning": str, "policy_clauses_applied": [str]}\n'
                "No markdown."
            )
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
        result["claim_id"] = claim_id
        result["claimant"] = claimant
        result["requested"] = amount
 
        if result["decision"] in ("approved", "partial"):
            self.total_approved = gl.u256(int(self.total_approved) + result["approved_amount"])
 
        self.claims[claim_id] = json.dumps(result)
        return result
 
    @gl.public.view
    def get_claim(self, claim_id: str) -> dict:
        if claim_id not in self.claims:
            return {}
        return json.loads(self.claims[claim_id])
 
    @gl.public.view
    def get_stats(self) -> dict:
        return {
            "total_claims": int(self.total_claims),
            "total_approved_tokens": int(self.total_approved),
        }
 
