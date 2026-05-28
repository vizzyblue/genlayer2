# CONTRACT 13 — On-Chain SLA Monitor
# Use-case: Fetches a service's status page and automatically triggers
# penalty payments when SLA thresholds are breached.
# =============================================================================
 
# { "Depends": "py-genlayer:latest" }
from genlayer import *
import json
 
class SLAMonitor(gl.Contract):
    service_name: str
    status_url: str
    client: gl.Address
    provider: gl.Address
    penalty_per_breach: gl.u256
    breach_count: gl.u256
    last_status: str
 
    def __init__(self, service_name: str, status_url: str,
                 provider: gl.Address, penalty_per_breach: int):
        self.service_name = service_name
        self.status_url = status_url
        self.client = gl.message.sender
        self.provider = provider
        self.penalty_per_breach = gl.u256(penalty_per_breach)
        self.breach_count = gl.u256(0)
        self.last_status = "unknown"
 
    @gl.public.write
    def check_sla(self) -> dict:
        """
        Fetches status page; LLM judges if SLA is breached and records it.
        """
        def nondet() -> str:
            response = gl.nondet.web.get(self.status_url)
            page = response.body.decode("utf-8")[:2000]
 
            prompt = (
                f"Service: {self.service_name}\n"
                f"Status page content:\n{page}\n\n"
                "Determine if the service is currently operational or experiencing an outage/degradation.\n"
                'Respond ONLY with JSON:\n'
                '{"status": "operational"|"degraded"|"outage", '
                '"sla_breached": true|false, "details": str, "severity": "none"|"low"|"high"}\n'
                "No markdown."
            )
            return gl.nondet.exec_prompt(prompt)
 
        raw = gl.eq_principle.strict_eq(nondet)
        result = json.loads(raw)
        self.last_status = result["status"]
 
        if result["sla_breached"]:
            self.breach_count = gl.u256(int(self.breach_count) + 1)
 
        return result
 
    @gl.public.view
    def get_breach_summary(self) -> dict:
        return {
            "service": self.service_name,
            "breach_count": int(self.breach_count),
            "total_penalty": int(self.breach_count) * int(self.penalty_per_breach),
            "last_status": self.last_status,
        }
 
 
