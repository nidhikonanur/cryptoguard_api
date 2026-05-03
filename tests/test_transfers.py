from __future__ import annotations


def test_valid_transfer_creation(client) -> None:
    response = client.post(
        "/transfers",
        json={
            "sender_account_id": "acct_100",
            "destination_address": "0xabc123456789def0",
            "asset_symbol": "BTC",
            "amount": 1250.5,
            "memo": "treasury rebalance",
            "idempotency_key": "transfer-key-001",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "approved"
    assert body["risk_score"] >= 0
    assert body["idempotent_replay"] is False


def test_invalid_asset_rejection(client) -> None:
    response = client.post(
        "/transfers",
        json={
            "sender_account_id": "acct_100",
            "destination_address": "0xabc123456789def0",
            "asset_symbol": "DOGE",
            "amount": 10,
            "memo": "test",
            "idempotency_key": "transfer-key-002",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "rejected"
    assert "unsupported asset" in body["risk_reasons"]


def test_duplicate_idempotency_returns_original_transfer(client) -> None:
    payload = {
        "sender_account_id": "acct_101",
        "destination_address": "0xabc123456789def0",
        "asset_symbol": "ETH",
        "amount": 50,
        "memo": "ops",
        "idempotency_key": "transfer-key-003",
    }

    first = client.post("/transfers", json=payload)
    second = client.post("/transfers", json=payload)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["idempotent_replay"] is True


def test_high_risk_transfer_is_flagged(client) -> None:
    response = client.post(
        "/transfers",
        json={
            "sender_account_id": "acct_risky",
            "destination_address": "xyz12345",
            "asset_symbol": "ETH",
            "amount": 30_000,
            "memo": "",
            "idempotency_key": "transfer-key-004",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] in {"flagged", "rejected"}
    assert body["risk_score"] >= 40
    assert any("suspicious" in reason or "large transfer" in reason for reason in body["risk_reasons"])
