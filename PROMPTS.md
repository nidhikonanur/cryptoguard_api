# PROMPTS.md

## Build Prompt

The initial build used the following prompt:

> You are helping me build an impressive backend software engineering portfolio project tailored for a crypto/fintech software engineering internship.
>
> Project name:
> cryptoguard_api
>
> Goal:
> Build a clean, production-minded backend API called CryptoGuard API. It should simulate risk checks for mock crypto transfers and trade orders before approving, rejecting, or flagging them for review. The project should demonstrate backend engineering, API design, security-conscious financial workflows, database modeling, idempotency, audit logging, testing, and performance awareness.
>
> Important:
> This is an original portfolio project. Do not use Gemini branding, logos, proprietary assets, real crypto wallets, real private keys, real exchange APIs, or real customer data. All data must be mocked.
>
> Target role requirements to optimize for:
> - backend software engineering
> - secure financial systems
> - API design
> - correctness and reliability
> - code quality and maintainability
> - testing and debugging
> - performance awareness
> - fintech / crypto interest
> - production-minded engineering
> - clear documentation
>
> Tech stack:
> - Python
> - FastAPI
> - SQLite by default, with clean repository/database abstraction
> - SQLAlchemy or SQLModel if appropriate
> - Pydantic models
> - pytest
> - optional: Docker
> - optional: simple latency benchmark script
>
> Core features:
> 1. API endpoints
>    - POST /transfers
>    - GET /transfers/{id}
>    - GET /audit-log
>    - POST /orders
>    - GET /orders/{id}
>    - GET /health
>
> 2. Mock crypto transfer workflow
>    A transfer should include:
>    - sender account id
>    - destination address
>    - asset symbol, such as BTC, ETH, SOL
>    - amount
>    - memo or note
>    - idempotency key
>
>    The service should:
>    - validate required fields
>    - reject unsupported assets
>    - reject non-positive amounts
>    - detect duplicate idempotency keys
>    - assign a deterministic risk score
>    - approve, reject, or flag the transfer
>
> 3. Mock trading order workflow
>    An order should include:
>    - account id
>    - symbol, such as BTC-USD or ETH-USD
>    - side: buy or sell
>    - quantity
>    - limit price
>    - idempotency key
>
>    The service should:
>    - validate required fields
>    - reject invalid side or quantity
>    - reject unsupported symbols
>    - detect duplicate idempotency keys
>    - assign a deterministic risk score
>    - approve, reject, or flag the order
>
> 4. Risk scoring
>    Implement deterministic rules such as:
>    - large transfer amount
>    - destination address format suspicious or too short
>    - missing memo
>    - unsupported asset
>    - repeated account activity
>    - unusually large order notional
>    - high-risk symbol if configured
>
> 5. Idempotency
>    Implement idempotency-key behavior so repeated requests with the same key do not create duplicate transfer/order records.
>
> 6. Audit logging
>    Every created transfer/order and every decision should write an audit log record with:
>    - timestamp
>    - event type
>    - entity type
>    - entity id
>    - decision
>    - risk score
>    - reason summary
>
> 7. Database design
>    Include tables/models for:
>    - transfers
>    - orders
>    - audit_logs
>    - idempotency records if needed
>
> 8. Tests
>    Add pytest tests for:
>    - valid transfer creation
>    - invalid asset rejection
>    - duplicate idempotency behavior
>    - high-risk transfer flagging
>    - valid order creation
>    - invalid order rejection
>    - audit log creation
>    - risk scoring logic
>
> 9. Performance awareness
>    Add a small script:
>    scripts/benchmark_latency.py
>
> 10. Documentation
>    Create a strong README.md with:
>    - project overview
>    - why I built it
>    - features
>    - architecture
>    - API endpoints
>    - database models
>    - risk scoring logic
>    - idempotency behavior
>    - audit logging
>    - security-conscious design choices
>    - setup instructions
>    - run instructions
>    - test instructions
>    - benchmark instructions
>    - example requests/responses
>    - limitations
>    - future improvements
>
> 11. PROMPTS.md
>    Create PROMPTS.md documenting:
>    - this build prompt
>    - any follow-up prompts used
>    - note that AI-assisted coding was used and all code/docs were reviewed and adapted

## Follow-up Prompts Used

No separate follow-up prompts were needed during the initial scaffold. The implementation was completed from the primary build prompt.

## AI Assistance Note

AI-assisted coding was used to accelerate scaffolding, implementation, and documentation. All generated code and documentation were reviewed, adapted, and organized for this portfolio project before being finalized.
