"""Regression tests for security and API behavior."""
import os

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from agents.base import AuditTrail, PHIGuard, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.api import app


def test_audit_entry_signature_is_checked_not_just_linkage():
    trail = AuditTrail(secret_key="testing-signature-integrity-key-2026")
    trail.log("system", "worker", "START", {"task_id": "DEMO-001"})
    trail.log("system", "worker", "COMPLETE", {"task_id": "DEMO-001"})
    assert trail.verify_integrity()
    trail.logs[1]["event_type"] = "ALTERED"
    assert not trail.verify_integrity()


def test_audit_metadata_delimiter_cannot_be_reassigned():
    trail = AuditTrail(secret_key="testing-signature-integrity-key-2026")
    trail.log("actor|tier", "unit", "START", {"task_id": "DEMO-001"})
    assert trail.verify_integrity()
    trail.logs[0]["actor"] = "actor"
    trail.logs[0]["actor_tier"] = "tier|unit"
    assert not trail.verify_integrity()


def test_audit_readers_receive_defensive_copies():
    trail = AuditTrail(secret_key="testing-signature-integrity-key-2026")
    receipt = trail.log("system", "worker", "START", {"task_id": "DEMO-001"})
    receipt["actor"] = "changed"
    exported = trail.get_trail()
    exported[0]["current_hash"] = "0" * 64
    assert trail.verify_integrity()


def test_audit_secret_file_minimum_length(tmp_path, monkeypatch):
    keyfile = tmp_path / "key"
    keyfile.write_text("short", encoding="utf-8")
    monkeypatch.delenv("AUDIT_SECRET_KEY", raising=False)
    monkeypatch.setenv("AUDIT_SECRET_KEY_FILE", str(keyfile))
    with pytest.raises(SecurityException):
        AuditTrail()


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_metrics_rejected(value):
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="DEMO-1", target_identifier="SYNTHETIC-1", primary_metric=value)


def test_nested_phi_and_actor_blocked():
    supervisor = SystemSupervisor()
    with pytest.raises(SecurityException):
        supervisor.process_task(SystemTaskPayload(
            task_id="DEMO", target_identifier="SYNTHETIC", primary_metric=10,
            attributes={"contact": "test@example.com"}))
    with pytest.raises(SecurityException):
        supervisor.process_task(SystemTaskPayload(
            task_id="DEMO", target_identifier="SYNTHETIC", primary_metric=10),
            actor="test@example.com")


def test_api_logs_fail_closed_and_authorized_access(monkeypatch):
    client = TestClient(app)
    monkeypatch.delenv("AUDIT_LOGS_TOKEN", raising=False)
    assert client.get("/api/audit/logs").status_code == 403
    monkeypatch.setenv("AUDIT_LOGS_TOKEN", "distinct-access-token")
    assert client.get("/api/audit/logs", headers={"X-Audit-Token": "wrong"}).status_code == 403
    response = client.get("/api/audit/logs", headers={"X-Audit-Token": "distinct-access-token"})
    assert response.status_code == 200
    assert response.json()["verified"] is True


def test_api_audit_rejects_nested_phi_and_accepts_synthetic_data():
    client = TestClient(app)
    payload = {
        "task_id": "DEMO-1", "target_identifier": "SYNTHETIC-1",
        "primary_metric": 26, "secondary_metric": 4, "status_descriptor": "NOMINAL"
    }
    assert client.post("/api/audit", json={**payload, "attributes": {"note": "MRN-123456"}}).status_code == 422
    response = client.post("/api/audit", json=payload)
    assert response.status_code == 200
    assert response.json()["overall_urgency"] == "ELEVATED_RISK"


def test_only_mock_llm_is_supported():
    from agents.llm_factory import LLMFactory
    with pytest.raises(ValueError, match="not implemented"):
        LLMFactory.create("openai")
