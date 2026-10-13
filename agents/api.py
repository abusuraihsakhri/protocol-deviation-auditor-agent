"""
FastAPI REST API Server for Protocol Deviation Auditor Agent.
"""
import time
import os
import hmac
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Response, Header
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor
from .metrics import GLOBAL_METRICS

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Protocol Deviation Auditor Agent API",
    description="Illustrative threshold evaluator. Not validated for clinical or GCP determinations.",
    version="2.0.1",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "protocol-deviation-auditor-agent", "domain": "Clinical & Biomedical AI", "standard": "Illustrative rules; no validated standard mapping", "version": "2.0.1"}


@app.get("/metrics")
def metrics():
    """Prometheus-compatible metrics endpoint."""
    return Response(
        content=GLOBAL_METRICS.export_prometheus_text(),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@app.get("/api/metrics/json")
def metrics_json():
    """JSON metrics endpoint for dashboards."""
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "DEMO"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    start = time.time()
    try:
        PHIGuard.assert_no_phi(payload.model_dump_json())
        dossier = supervisor.process_task(payload)
        duration = time.time() - start
        GLOBAL_METRICS.record_task(dossier.overall_urgency.value, duration)
        return dossier.to_dict()
    except SecurityException as e:
        GLOBAL_METRICS.record_phi_block()
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException as e:
        GLOBAL_METRICS.record_phi_block()
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs(x_audit_token: str = Header(default="")):
    """Do not disclose audit metadata without an explicitly configured access token."""
    required = os.getenv("AUDIT_LOGS_TOKEN", "")
    if not required or not hmac.compare_digest(required, x_audit_token):
        raise HTTPException(status_code=403, detail="Audit log access is disabled or unauthorized.")
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
