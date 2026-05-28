# CONTRACT 19 — AI Ethical Compliance Checker
# Use-case: Companies submit AI system descriptions; LLM checks them against
# ethical AI principles (EU AI Act, IEEE standards) and scores compliance.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
import hashlib
 
class EthicsComplianceChecker(gl.Contract):
    standard: str
    compliance_reports: TreeMap[str, str]
    total_checks: gl.u256
 
    def __init__(self, standard: str):
        # standard: "EU_AI_ACT" | "IEEE_7000" | "NIST_AI_RMF"
        self.standard = standard
        self.total_checks = gl.u256(0)
 
    @gl.public.write
    def check_compliance(self, system_description: str, use_case: str) -> dict:
        """
        Evaluates an AI system's description for ethical compliance.
        """
        doc_hash = hashlib.sha256(f"{system_description}{use_case}".encode()).hexdigest()[:20]
        if doc_hash in self.compliance_reports:
            return json.loads(self.compliance_reports[doc_hash])
 
        self.total_checks = gl.u256(int(self.total_checks) + 1)
 
        prompt = (
            f"Ethical Standard: {self.standard}\n"
            f"Use Case: {use_case}\n\n"
            f"AI System Description:\n{system_description}\n\n"
            f"Evaluate this AI system's compliance with {self.standard}.\n"
            "Check: transparency, fairness, accountability, privacy, safety, human oversight.\n"
            'Respond ONLY with JSON:\n'
            '{"overall_score": int(0-100), "compliant": true|false, '
            '"dimensions": {"transparency": int, "fairness": int, "accountability": int, '
            '"privacy": int, "safety": int, "oversight": int}, '
            '"violations": [str], "recommendations": [str], "risk_level": "low"|"medium"|"high"}\n'
            "No markdown."
        )
 
        def nondet() -> str:
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
        self.compliance_reports[doc_hash] = json.dumps(result)
        return result
 
    @gl.public.view
    def get_report(self, doc_hash: str) -> dict:
        if doc_hash not in self.compliance_reports:
            return {}
        return json.loads(self.compliance_reports[doc_hash])
 
