# CONTRACT 14 — DAO Conflict Resolver
# Use-case: When DAO members submit conflicting proposals, the LLM mediates,
# finds common ground, and proposes a merged resolution.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
 
class DAOConflictResolver(gl.Contract):
    dao_name: str
    conflicts: TreeMap[str, str]
    conflict_count: gl.u256
 
    def __init__(self, dao_name: str):
        self.dao_name = dao_name
        self.conflict_count = gl.u256(0)
 
    @gl.public.write
    def resolve_conflict(self, proposal_a: str, proposal_b: str, context: str) -> dict:
        """
        Mediates between two conflicting DAO proposals and returns a merged solution.
        """
        self.conflict_count = gl.u256(int(self.conflict_count) + 1)
        conflict_id = f"conflict_{int(self.conflict_count)}"
 
        prompt = (
            f"DAO: {self.dao_name}\n"
            f"Context: {context}\n\n"
            f"Proposal A: {proposal_a}\n\n"
            f"Proposal B: {proposal_b}\n\n"
            "You are a neutral mediator. Find the common ground between these proposals.\n"
            "Propose a merged resolution that honors the core intent of both.\n"
            'Respond ONLY with JSON:\n'
            '{"merged_proposal": str, "rationale": str, '
            '"concessions_A": [str], "concessions_B": [str], "alignment_score": int(0-100)}\n'
            "No markdown."
        )
 
        def nondet() -> str:
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
        result["conflict_id"] = conflict_id
        self.conflicts[conflict_id] = json.dumps(result)
        return result
 
    @gl.public.view
    def get_resolution(self, conflict_id: str) -> dict:
        if conflict_id not in self.conflicts:
            return {}
        return json.loads(self.conflicts[conflict_id])
 
 
