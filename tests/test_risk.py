from __future__ import annotations

from app.risk import AccountActivitySnapshot, score_order, score_transfer
from app.schemas import OrderCreate, TransferCreate


def test_transfer_risk_scoring_logic() -> None:
    payload = TransferCreate(
        sender_account_id="acct_300",
        destination_address="short123",
        asset_symbol="BTC",
        amount=50_000,
        memo=None,
        idempotency_key="transfer-risk-001",
    )

    result = score_transfer(payload, AccountActivitySnapshot(transfer_count=4, order_count=1))

    assert result.decision in {"flagged", "rejected"}
    assert result.score >= 40
    assert "repeated account activity" in result.reasons


def test_order_risk_scoring_logic() -> None:
    payload = OrderCreate(
        account_id="acct_301",
        symbol="SOL-USD",
        side="buy",
        quantity=200,
        limit_price=300,
        idempotency_key="order-risk-001",
    )

    result = score_order(payload, AccountActivitySnapshot(transfer_count=0, order_count=0))

    assert result.decision == "flagged"
    assert result.score >= 40
    assert "symbol is configured as high risk" in result.reasons
