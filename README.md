# CryptoGuard API

CryptoGuard API is a backend portfolio project for a crypto and fintech software engineering internship. It simulates pre-trade and pre-transfer risk checks for mock crypto operations, then approves, flags, or rejects requests using deterministic rules and a complete audit trail.

## Why I Built It

I wanted a project that demonstrates production-minded backend engineering in a financial context without relying on real wallets, real exchange APIs, or real customer data. The goal is to show API design, correctness, reliability, testing, auditability, and security-aware workflow thinking in a compact but complete service.

## Features

- FastAPI service with typed request and response models
- Mock crypto transfer workflow with deterministic risk scoring
- Mock trade order workflow with deterministic risk scoring
- Idempotency-key support to prevent duplicate creates
- Audit logging for entity creation and decisions
- SQLite persistence with SQLAlchemy and clear repository boundaries
- Pytest coverage for core API and risk behavior
- Simple local latency benchmark for the risk engine

## Architecture

The project is organized into focused backend layers:

- `app/main.py`: FastAPI app setup and route registration
- `app/db.py`: database engine, session lifecycle, and metadata initialization
- `app/models.py`: SQLAlchemy tables for transfers, orders, audit logs, and idempotency records
- `app/schemas.py`: Pydantic request and response contracts
- `app/risk.py`: deterministic risk engine and scoring rules
- `app/services.py`: repository abstractions, idempotency enforcement, and audit writes
- `app/routes/`: HTTP route handlers for transfers, orders, and audit retrieval
- `tests/`: API and risk-engine test coverage
- `scripts/benchmark_latency.py`: latency measurements for the local scoring path

## API Endpoints

- `POST /transfers`
- `GET /transfers/{id}`
- `POST /orders`
- `GET /orders/{id}`
- `GET /audit-log`
- `GET /health`

## Database Models

### `transfers`
- `id`
- `sender_account_id`
- `destination_address`
- `asset_symbol`
- `amount`
- `memo`
- `idempotency_key`
- `status`
- `risk_score`
- `risk_reasons`
- `created_at`

### `orders`
- `id`
- `account_id`
- `symbol`
- `side`
- `quantity`
- `limit_price`
- `idempotency_key`
- `status`
- `risk_score`
- `risk_reasons`
- `created_at`

### `audit_logs`
- `timestamp`
- `event_type`
- `entity_type`
- `entity_id`
- `decision`
- `risk_score`
- `reason_summary`

### `idempotency_records`
- `entity_type`
- `idempotency_key`
- `request_hash`
- `entity_id`
- `created_at`

## Risk Scoring Logic

The risk engine is deterministic so the same payload and account activity state produce the same result.

### Transfer rules
- Reject unsupported assets
- Increase score for large transfer amounts
- Increase score for suspiciously short destination addresses
- Increase score for unusual destination address prefixes
- Increase score when memo is missing
- Increase score for repeated account activity

### Order rules
- Reject unsupported symbols
- Increase score for large order notional
- Increase score for symbols configured as high risk
- Increase score for large quantities
- Increase score for repeated account activity

### Decision thresholds
- `approved`: score below 40
- `flagged`: score from 40 to 79
- `rejected`: score 80+ or hard-reject rule triggered

## Idempotency Behavior

Both create endpoints require an `idempotency_key`.

- If a key is new, the API creates a new record and stores a hash of the request payload.
- If the same key is reused with the same payload, the API returns the original record instead of creating a duplicate.
- If the same key is reused with a different payload, the API returns `409 Conflict`.

This mirrors the kind of duplicate-protection behavior commonly used in financial APIs.

## Audit Logging

Each successful create flow writes audit entries for:

- the creation event
- the final risk decision

Idempotent replays also write an audit event for observability.

## Security-Conscious Design Choices

- All data is mocked. There are no real wallets, private keys, exchange credentials, or customer records.
- Inputs are validated with Pydantic constraints before service execution.
- Risk decisions are explainable through explicit reasons.
- Idempotency protects against accidental duplicate submission.
- Audit records preserve important state transitions for debugging and review.
- In a production system, authentication and authorization would be added at the API boundary before route execution.
- In a production system, encrypted secret storage would be used for any integration credentials.
- In a production system, rate limiting and abuse controls would be added at the gateway or application layer.
- In a production system, transaction signing and wallet controls would live in a separate hardened subsystem.

## Setup Instructions

```bash
cd /Users/nidhikonanur/Documents/Playground/cryptoguard_api
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python `3.12` is the recommended local version for this project. On this machine, `3.14` caused dependency compatibility issues with the pinned Pydantic stack.

## Run Instructions

```bash
cd /Users/nidhikonanur/Documents/Playground/cryptoguard_api
source .venv/bin/activate
uvicorn app.main:app --reload
```

Open the API docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Test Instructions

```bash
cd /Users/nidhikonanur/Documents/Playground/cryptoguard_api
source .venv/bin/activate
pytest
```

## Benchmark Instructions

```bash
cd /Users/nidhikonanur/Documents/Playground/cryptoguard_api
source .venv/bin/activate
PYTHONPATH=. python scripts/benchmark_latency.py
```

## Example Requests and Responses

### Create a transfer

```bash
curl -X POST http://127.0.0.1:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "sender_account_id": "acct_100",
    "destination_address": "0xabc123456789def0",
    "asset_symbol": "BTC",
    "amount": 1250.5,
    "memo": "treasury rebalance",
    "idempotency_key": "transfer-key-001"
  }'
```

Example response:

```json
{
  "id": 1,
  "sender_account_id": "acct_100",
  "destination_address": "0xabc123456789def0",
  "asset_symbol": "BTC",
  "amount": 1250.5,
  "memo": "treasury rebalance",
  "idempotency_key": "transfer-key-001",
  "status": "approved",
  "risk_score": 0,
  "risk_reasons": ["passed baseline transfer checks"],
  "created_at": "2026-05-03T00:00:00Z",
  "idempotent_replay": false
}
```

### Create an order

```bash
curl -X POST http://127.0.0.1:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "acct_200",
    "symbol": "BTC-USD",
    "side": "buy",
    "quantity": 0.5,
    "limit_price": 65000,
    "idempotency_key": "order-key-001"
  }'
```

Example response:

```json
{
  "id": 1,
  "account_id": "acct_200",
  "symbol": "BTC-USD",
  "side": "buy",
  "quantity": 0.5,
  "limit_price": 65000,
  "idempotency_key": "order-key-001",
  "status": "approved",
  "risk_score": 0,
  "risk_reasons": ["passed baseline order checks"],
  "created_at": "2026-05-03T00:00:00Z",
  "idempotent_replay": false
}
```

## Limitations

- This service is intentionally mocked and should not be used for real money movement.
- Authentication, authorization, and rate limiting are documented but not implemented.
- SQLite is appropriate for local development and portfolio demos, not high-scale deployment.
- Risk scoring is rules-based and deterministic, not adaptive or market-aware.
- No background jobs, streaming events, or external ledger integration are included.

## Future Improvements

- Add API-key authentication and role-based authorization
- Add Alembic migrations
- Add structured logging and metrics export
- Add Redis-backed idempotency or caching
- Add pagination and filtering for audit logs
- Add Docker and CI workflow files
- Add asynchronous outbox events for downstream review workflows
