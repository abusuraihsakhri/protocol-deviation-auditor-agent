"""
FastAPI REST API Server for Protocol Deviation Auditor Agent.
"""
import time
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor
from .metrics import GLOBAL_METRICS

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Protocol Deviation Auditor Agent API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "protocol-deviation-auditor-agent", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


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
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    start = time.time()
    try:
        PHIGuard.assert_no_phi(payload.task_id)
        PHIGuard.assert_no_phi(payload.target_identifier)
        PHIGuard.assert_no_phi(payload.status_descriptor)
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
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
