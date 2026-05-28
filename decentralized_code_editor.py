# CONTRACT 17 — Decentralized Code Auditor
# Use-case: Developers submit code snippets for security auditing; LLM
# identifies vulnerabilities, anti-patterns, and rates severity.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
import hashlib
 
class CodeAuditor(gl.Contract):
    audit_reports: TreeMap[str, str]
    total_audits: gl.u256
 
    def __init__(self):
        self.total_audits = gl.u256(0)
 
    @gl.public.write
    def audit_code(self, code_snippet: str, language: str) -> dict:
        """
        Audits code for security vulnerabilities using LLM consensus.
        """
        code_hash = hashlib.sha256(code_snippet.encode()).hexdigest()[:20]
        if code_hash in self.audit_reports:
            return json.loads(self.audit_reports[code_hash])
 
        self.total_audits = gl.u256(int(self.total_audits) + 1)
 
        prompt = (
            f"Language: {language}\n\n"
            f"Code to audit:\n```{language}\n{code_snippet}\n```\n\n"
            "Identify security vulnerabilities, logic errors, and anti-patterns.\n"
            "Rate overall severity: critical/high/medium/low/none.\n"
            'Respond ONLY with JSON:\n'
            '{"severity": "critical"|"high"|"medium"|"low"|"none", '
            '"security_score": int(0-100), '
            '"vulnerabilities": [{"name": str, "line": str, "severity": str, "fix": str}], '
            '"anti_patterns": [str], "summary": str}\n'
            "No markdown."
        )
 
        def nondet() -> str:
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
        result["code_hash"] = code_hash
        result["language"] = language
        self.audit_reports[code_hash] = json.dumps(result)
        return result
 
    @gl.public.view
    def get_report(self, code_hash: str) -> dict:
        if code_hash not in self.audit_reports:
            return {}
        return json.loads(self.audit_reports[code_hash])
