# Protocol Deviation Auditor Agent

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Protocol Deviation Auditor Agent

---

## ⚙️ Key Capabilities & Algorithmic Modules

- **Deterministic Calculation Engine**: Strict compliance with standard reference formulations and thresholds.
- **Risk & Urgency Classification**: Multi-tier categorization with automated clinical/operational action recommendations.
- **Validation & Guardrails**: Rigorous input bounds checking and anomaly detection.

---

## 🔧 Configuration

The application requires an HMAC-SHA256 audit secret key. Set it via environment variable:

```bash
# Linux/macOS
export AUDIT_SECRET_KEY="your-secure-random-key-min-16-chars"

# Windows
set AUDIT_SECRET_KEY=your-secure-random-key-min-16-chars
```

Or copy `.env.example` to `.env` and set it there for Docker deployments.

## 💻 CLI Quickstart & Usage

### 1. Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Batch CSV Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 3. Supervisory Chat
```bash
python cli.py chat "What is the system status?"
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
- `--task-id`: Unique task/case identifier (required for audit)
- `--target`: Target entity or specimen identifier
- `--primary`: Primary measurement value (float)
- `--secondary`: Secondary measurement value (float)
- `--critical`: Flag for critical/emergency escalation
- `--status`: Status descriptor (e.g., NOMINAL, DISCORDANT, ANOMALY)
- `-i/--input`: Input CSV file path (for batch mode)
- `-o/--output`: Output CSV file path (for batch mode)

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `task_id` | Unique task/case identifier | Required |
| `target_identifier` | Target entity or specimen identifier | Required |
| `primary_metric` | Primary measurement value (float) | Required |
| `secondary_metric` | Secondary measurement value (float) | Optional (default: 0.0) |
| `is_critical_flag` | Emergency escalation flag | Optional (default: false) |
| `status_descriptor` | Status or phenotype descriptor | Optional (default: NOMINAL) |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

The test suite automatically configures the audit secret via `tests/conftest.py`.

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

Run the security audit:

```bash
python -c "from agents.base import PHIGuard, AuditLogger; print('PHI Guard & Audit:', PHIGuard.redact_phi('test'), '|', AuditLogger.verify_integrity())"
```

---

## 🐳 Container Deployment

### Docker Compose (recommended)
```bash
cp .env.example .env
# Edit .env to set a secure AUDIT_SECRET_KEY
docker-compose up --build
```

### Docker directly
```bash
docker build -t protocol-deviation-auditor-agent .
docker run -e AUDIT_SECRET_KEY="your-secure-key-here" -p 8000:8000 protocol-deviation-auditor-agent
```
