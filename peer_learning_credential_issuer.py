# CONTRACT 20 — Peer Learning Credential Issuer
# Use-case: Students complete peer reviews; LLM validates the quality of their
# peer feedback and issues verifiable on-chain credentials.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
 
class PeerCredentialIssuer(gl.Contract):
    course_name: str
    credentials: TreeMap[str, str]
    total_issued: gl.u256
 
    def __init__(self, course_name: str):
        self.course_name = course_name
        self.total_issued = gl.u256(0)
 
    @gl.public.write
    def submit_peer_review(self, student_work: str, peer_feedback: str, rubric: str) -> dict:
        """
        Validates peer review quality; issues credential if feedback meets standards.
        """
        reviewer = str(gl.message.sender)
 
        prompt = (
            f"Course: {self.course_name}\n"
            f"Grading Rubric: {rubric}\n\n"
            f"Student Work Reviewed:\n{student_work[:1000]}\n\n"
            f"Peer Feedback Provided:\n{peer_feedback}\n\n"
            "Assess whether the peer feedback is thorough, constructive, and rubric-aligned.\n"
            "Should a credential be issued to the reviewer?\n"
            'Respond ONLY with JSON:\n'
            '{"credential_issued": true|false, "quality_score": int(0-100), '
            '"thoroughness": int, "constructiveness": int, "rubric_alignment": int, '
            '"credential_level": "bronze"|"silver"|"gold"|"none", "feedback_on_feedback": str}\n'
            "No markdown."
        )
 
        def nondet() -> str:
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
        result["reviewer"] = reviewer
        result["course"] = self.course_name
 
        if result["credential_issued"]:
            self.total_issued = gl.u256(int(self.total_issued) + 1)
            self.credentials[reviewer] = json.dumps(result)
 
        return result
 
    @gl.public.view
    def get_credential(self, reviewer_address: str) -> dict:
        if reviewer_address not in self.credentials:
            return {}
        return json.loads(self.credentials[reviewer_address])
 
