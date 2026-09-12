# Epiderm Clinic Service

FastAPI clinic engine for AI-assisted skin and hair consults. Patients submit questionnaires (and optional images); workers generate a diagnosis via a local Ollama LLM.

## Current Scope

Implemented:

- **Questionnaires** — Active template by category (`SKIN` / `HAIR`), cached in Redis. Submit creates a consult (Postgres), stores the response (MongoDB), and enqueues async processing.
- **Consults** — Create and list. Status advances through AI diagnosis (`CREATED` → `QUESTIONNAIRE_SUBMITTED` → `DRAI_DG_PENDING` → `DRAI_DG_PROCESSING` → `DRAI_DG_DIAGNOSED`). Later payment, doctor review, and kit statuses exist on the model but are not driven by APIs yet.
- **Diagnoses** — Sync LLM calls and async Celery jobs (text / vision / multimodal). Results persist in MongoDB and can be read by consult or job id.
- **Auth** — Client routes: Bearer JWT (`sub` = patient id). Internal S2S routes: `X-API-Key`.

Not implemented (stubs or out of scope for now): prescriptions, medicine kits, paywall, doctor review, fulfillment.

Workers:

| Process | Queue | Role |
| --- | --- | --- |
| `consumer` | `questionnaire_submitted` | Load the Mongo response, set consult to `DRAI_DG_PROCESSING`, enqueue diagnosis |
| `worker` | `diagnosis_ready` | Call Ollama and persist the diagnosis |

## Quick Start (App & Workers)

Requires Docker, Python 3.11+, and a running [Ollama](https://ollama.com/) instance with the models in `.env.example` (defaults: `llama3.2`, `gemma3:12b`).

```bash
cp .env.example .env
```

Set `S2S_API_KEY` and `JWT_SECRET_KEY` in `.env`. Keep `JWT_SECRET_KEY` aligned with the issuer of client tokens.

### Docker (API + workers + datastores)

```bash
docker compose up --build
```

- API: `http://localhost:8000`
- Health: `GET /` and `GET /health` (Postgres, MongoDB, Redis)
- Docs: `http://localhost:8000/docs`

Compose starts Postgres, MongoDB, Redis, the API, the questionnaire consumer, and the diagnosis worker. The diagnosis worker reaches Ollama on the host via `OLLAMA_HOST` (default `http://host.docker.internal:11434`).

### Local API and workers

Start Postgres, MongoDB, and Redis so they match `.env` (`localhost` URLs). Compose currently publishes Postgres (`5432`) and Mongo (`27017`) only; Redis is internal to the Compose network unless you add a host port or run Redis locally.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Questionnaire consumer:

```bash
celery -A app.core.celery_app worker -Q questionnaire_submitted -n consumer@%h --pool=solo --loglevel=info
```

Diagnosis worker (needs Ollama):

```bash
celery -A app.core.celery_app worker -Q diagnosis_ready -n worker@%h --pool=solo --loglevel=info
```

Inspect a queue (Redis list) or worker state:

```bash
redis-cli LLEN questionnaire_submitted
celery -A app.core.celery_app inspect active
celery -A app.core.celery_app inspect reserved
```

## Brief Usage

Base path: `/api/v1`. Client calls use `Authorization: Bearer <jwt>`. Internal calls use `/api/v1/internal/...` plus `X-API-Key`.

1. **Active questionnaire** — `GET /api/v1/questionnaire/?category=SKIN` (or `HAIR`).
2. **Submit** — `POST /api/v1/questionnaire/` with `category`, optional `questionnaire`, optional base64 `images`. Returns `202` with `consult_id`, `status` (`DRAI_DG_PENDING`), and `task_id`.
3. **Poll diagnosis** — `GET /api/v1/diagnosis/consult/{consult_id}` or `GET /api/v1/diagnosis/jobs/{job_id}`.
4. **Consults** — `GET /api/v1/consult/?consult_id=...` or `GET /api/v1/consult/{consult_id}` (single consult + Mongo `diagnosis_result`). List: `GET /api/v1/consult/all` or `GET /api/v1/consult/patient/{patient_id}`.

Direct (non-submit) diagnosis:

- Sync: `POST /api/v1/diagnosis/text|vision|multimodal`
- Async: `POST /api/v1/diagnosis/jobs/text|vision|multimodal` then poll `/jobs/{job_id}`

S2S extras: list all questionnaire versions, Redis cache refresh/invalidate under `/api/v1/internal/questionnaire/`.
