"""
Command-Line Interface for ICH-GCP Protocol Deviation & Good Clinical Practice Auditor Agent.
"""
import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path
from .models import FrontierPayload
from .agents import GCPProtocolCoordinator

coordinator = GCPProtocolCoordinator()


class SecurityException(Exception):
    """Raised when input violates security constraints."""
    pass


def _safe_resolve_path(file_path: str, must_exist: bool = False) -> Path:
    """Resolve a path safely, preventing directory traversal outside CWD."""
    cwd = Path.cwd().resolve()
    resolved = (cwd / file_path).resolve()
    if not str(resolved).startswith(str(cwd) + os.sep) and resolved != cwd:
        raise SecurityException(f"Path traversal blocked: '{file_path}' escapes working directory")
    if must_exist and not resolved.is_file():
        raise FileNotFoundError(f"Input file not found: '{file_path}'")
    return resolved


def _sanitize_id(value: str, field_name: str, max_len: int = 128) -> str:
    """Sanitize identifier fields to prevent injection."""
    if not value or not value.strip():
        raise SecurityException(f"{field_name} cannot be empty")
    cleaned = value.strip()
    if len(cleaned) > max_len:
        raise SecurityException(f"{field_name} exceeds maximum length of {max_len}")
    if re.search(r'[\x00-\x1f\x7f\\/:*?"<>|]', cleaned):
        raise SecurityException(f"{field_name} contains invalid characters")
    return cleaned


def main(argv=None):
    parser = argparse.ArgumentParser(prog="protocol-deviation-auditor-agent", description="ICH-GCP Protocol Deviation & Good Clinical Practice Auditor Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single task evaluation")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="TARGET-GEN-01")
    p_audit.add_argument("--primary", type=float, default=29.4)
    p_audit.add_argument("--secondary", type=float, default=15.1)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        payload = FrontierPayload(
            task_id=_sanitize_id(args.task_id, "task_id"),
            target_identifier=_sanitize_id(args.target, "target_identifier"),
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=_sanitize_id(args.status, "status_descriptor"),
            is_critical_flag=args.critical,
        )
        dossier = coordinator.process(payload)
        print("=" * 80)
        print(f"  ICH-GCP PROTOCOL DEVIATION & GOOD CLINICAL PRACTICE AUDITOR AGENT")
        print(f"  Domain: Clinical Trials | Standard: ICH E6(R2) Good Clinical Practice")
        print(f"  Task: {dossier['task_id']} | Status: [{dossier['overall_status']}] | Total Alerts: {dossier['total_alerts']}")
        print("=" * 80)
        for a in dossier["alerts"]:
            print(f"\n  [{a['status']}] from {a['origin_agent']}:")
            print(f"  Summary: {a['summary']}")
            print(f"  Details: {a['technical_details']}")
            print(f"  Action:  {a['actionable_remediation']}")
        print("\n" + "=" * 80)
        return 0

    if args.command == "chat":
        ans = coordinator.query_supervisory_chat(" ".join(args.query))
        print(f"\n[GCPProtocolCoordinator]:\n{ans}\n")
        return 0

    if args.command == "batch":
        in_path = _safe_resolve_path(args.input, must_exist=True)
        out_path = _safe_resolve_path(args.output)

        with open(in_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        out_fields = fieldnames + ["overall_status", "total_alerts", "critical_count", "consensus_summary"]
        out_rows = []
        for r in rows:
            payload = FrontierPayload(
                task_id=_sanitize_id(str(r.get("task_id", "TASK-01")), "task_id"),
                target_identifier=_sanitize_id(str(r.get("target_identifier", "TARGET-01")), "target_identifier"),
                primary_metric=float(r.get("primary_metric", 15.0)),
                secondary_metric=float(r.get("secondary_metric", 5.0)),
                status_descriptor=_sanitize_id(str(r.get("status_descriptor", "NOMINAL")), "status_descriptor"),
                is_critical_flag=str(r.get("is_critical_flag", "False")).lower() in ("true", "1", "yes"),
            )
            dossier = coordinator.process(payload)
            row_dict = dict(r)
            row_dict["overall_status"] = dossier["overall_status"]
            row_dict["total_alerts"] = dossier["total_alerts"]
            row_dict["critical_count"] = dossier["critical_count"]
            row_dict["consensus_summary"] = dossier["consensus_summary"]
            out_rows.append(row_dict)

        with open(out_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"Processed {len(out_rows)} records -> {out_path}")
        return 0

    if args.command == "serve":
        try:
            import uvicorn
            from .server import create_app
            app = create_app()
            if app:
                print(f"Starting ICH-GCP Protocol Deviation & Good Clinical Practice Auditor Agent on http://{args.host}:{args.port}")
                uvicorn.run(app, host=args.host, port=args.port)
        except ImportError:
            print("FastAPI / uvicorn not installed. Run 'pip install fastapi uvicorn'")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
