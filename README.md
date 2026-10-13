# Protocol Deviation Auditor Agent

An example-rule evaluator for synthetic clinical-trial operational data. The repository contains a Python CLI, REST API, a legacy ICH-GCP-themed evaluator, and a **fully local browser demonstration**.

**Scope:** This software is a prototype, not a validated GCP compliance, clinical decision-support, or medical-device tool. The numeric boundaries and descriptor keywords are examples from the source code, **not** visit-window, eligibility, investigational-product, or adverse-event rules derived from a study protocol. The older engine cites ICH E6(R2); [ICH E6(R3)](https://www.ema.europa.eu/en/scientific-guidelines/ich-e6-good-clinical-practice) is the newer guideline. Neither version is implemented as a comprehensive ruleset.

## Browser demonstration

Serve the `web/` directory locally or use the published static site when available:

```bash
python -m http.server 8001 --directory web
# Open http://localhost:8001/
```

ES modules may be blocked when opening the HTML directly through `file://`. Enter **only synthetic IDs and values**, run the example rules, inspect alerts, and optionally download the JSON result.

- Runs directly in JavaScript; **no Python runtime or backend connection** is required.
- Primary metric above **25**: elevated warning.
- Secondary metric above **12**: elevated warning; the explicit critical flag takes precedence.
- Status descriptors containing `DISCORDANT`, `ANOMALY`, `MUTANT`, `VIOLATION`, `FAIL`, or `REJECT`: elevated warning.
- This page produces **no cryptographically signed audit trail**. Counters are for the current page session only.

## Python CLI and API

Requires Python 3.10–3.12 for the tested workflow. Install from the repository:

```bash
python -m pip install -e ".[api,test]"
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
python cli.py audit --task-id DEMO-001 --target SYNTHETIC-01 --primary 28.5 --secondary 14.2 --status DISCORDANT
python cli.py batch --input sample.csv --output results.csv
python cli.py verify-audit
python cli.py serve --host 127.0.0.1 --port 8000
```

On Windows, set `AUDIT_SECRET_KEY` in your environment using the shell's appropriate syntax. The API documents its endpoints at `http://127.0.0.1:8000/docs`, including `POST /api/audit`, `POST /api/chat`, `GET /health`, and `GET /metrics`.

`GET /api/audit/logs` returns **403 by default**. To enable audit metadata retrieval, set an unpredictable `AUDIT_LOGS_TOKEN` and send its value in the `X-Audit-Token` request header. Do not publish this service to the Internet without additional authentication, TLS and an appropriate security review.

The `agents/` implementation powers `cli.py` and `agents.api`. The `gcp_protocol_auditor/` implementation is a separate legacy evaluator, accessible via `python -m gcp_protocol_auditor.cli` or the installed `protocol-deviation-auditor-engine` entry point. Their thresholds and output formats differ; they should not be treated as interchangeable.

## Privacy and audit limitations

- **Never enter patient data or PHI.** The Python service performs limited, pattern-based identifier screening, which is **not** HIPAA Safe Harbor de-identification or a guarantee against PHI exposure.
- The browser demonstration does not upload or store inputs. JSON downloads are explicitly requested by the user. No analytics or remote fonts are included.
- The Python evaluator holds dossiers and the HMAC-chain entries **in process memory**. The signed chain covers audit metadata and a payload digest but is **not durable**, externally timestamped, or independently compliant with regulated record-keeping requirements.
- The `AUDIT_SECRET_KEY` is required for the Python `agents/` implementation. Keep it outside source control. `.env.example` contains blank secret placeholders.

## Docker

```bash
cp .env.example .env
# Set AUDIT_SECRET_KEY in .env to a unique high-entropy value.
docker compose up --build
```

The Compose service binds to `127.0.0.1:8000` by default. The `.dockerignore` prevents `.env` and local secrets from entering the build context.

## Verification

```bash
python -m pytest -q
node --check web/audit.mjs
node --test tests/web.test.mjs
```

The GitHub Actions test matrix covers Python 3.10, 3.11 and 3.12, with separate JavaScript tests. For deployment, the `Publish browser demo` workflow uploads the `web/` directory to GitHub Pages if Pages deployment is enabled in repository settings.

## Technology and license

Python, Pydantic 2, optional FastAPI/Uvicorn, standard-library HMAC-SHA256, and browser-native JavaScript (ES modules). The browser demonstration requires a modern Chromium, Firefox or Safari release. Licensed under [MIT](LICENSE).
