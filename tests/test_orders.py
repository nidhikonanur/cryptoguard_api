from __future__ import annotations


def test_valid_order_creation(client) -> None:
    response = client.post(
        "/orders",
        json={
            "account_id": "acct_200",
            "symbol": "BTC-USD",
            "side": "buy",
            "quantity": 0.5,
            "limit_price": 65000,
            "idempotency_key": "order-key-001",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "approved"
    assert body["idempotent_replay"] is False


def test_invalid_order_rejection(client) -> None:
    response = client.post(
        "/orders",
        json={
            "account_id": "acct_201",
            "symbol": "XRP-USD",
            "side": "sell",
            "quantity": 1,
            "limit_price": 2.15,
            "idempotency_key": "order-key-002",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "rejected"
    assert "unsupported symbol" in body["risk_reasons"]


def test_duplicate_idempotency_returns_original_order(client) -> None:
    payload = {
        "account_id": "acct_202",
        "symbol": "ETH-USD",
        "side": "sell",
        "quantity": 2,
        "limit_price": 3200,
        "idempotency_key": "order-key-003",
    }

    first = client.post("/orders", json=payload)
    second = client.post("/orders", json=payload)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["idempotent_replay"] is True
