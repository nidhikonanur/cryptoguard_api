# CryptoGuard API

CryptoGuard API is a backend portfolio project that simulates pre-trade and pre-transfer risk checks for mock crypto workflows. It scores each request with deterministic rules, records audit events, and returns an approval, flag, or rejection decision through a FastAPI service.

## What It Demonstrates

- API design with typed request and response models
- Deterministic rules-based risk scoring
- Idempotent create endpoints
- Audit logging for important state transitions
- Clear separation between routing, services, persistence, and scoring logic
- Testable backend architecture for finance-flavored workflows

## Features

- Transfer risk evaluation
- Order risk evaluation
- SQLite persistence with SQLAlchemy
- Idempotency protection for create requests
- Audit log retrieval
- Health endpoint and local benchmark script

## API Endpoints

- `POST /transfers`
- `GET /transfers/{id}`
- `POST /orders`
- `GET /orders/{id}`
- `GET /audit-log`
- `GET /health`

## Risk Model

### Transfer checks

- unsupported assets
- unusually large amounts
- suspicious destination addresses
- missing memos
- repeated account activity

### Order checks

- unsupported symbols
- large notional values
- high-risk configured symbols
- unusually large quantities
- repeated account activity

### Decision thresholds

- `approved`: score below 40
- `flagged`: score from 40 to 79
- `rejected`: score 80+ or hard-reject condition

## Idempotency Behavior

Both create endpoints require an `idempotency_key`.

- Same key plus same payload returns the original record.
- Same key plus different payload returns `409 Conflict`.
- New key creates a fresh record.

## Local Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python `3.12` is the recommended local version for this project.

## Run Locally

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

API docs are available at `http://127.0.0.1:8000/docs`.

## Tests

```bash
source .venv/bin/activate
pytest
```

## Benchmark

```bash
source .venv/bin/activate
PYTHONPATH=. python scripts/benchmark_latency.py
```

## Safety Notes

- All data is mocked.
- No real wallets, private keys, or exchange credentials are used.
- This project is for local development, experimentation, and portfolio demonstration.

## Limitations

- No authentication or authorization layer is implemented yet.
- SQLite is suitable for demos, not high-scale production use.
- The scoring model is deterministic and intentionally simple.
