from __future__ import annotations


def test_audit_log_creation(client) -> None:
    create_response = client.post(
        "/transfers",
        json={
            "sender_account_id": "acct_audit",
            "destination_address": "0xabc123456789def0",
            "asset_symbol": "BTC",
            "amount": 100,
            "memo": "audit test",
            "idempotency_key": "transfer-audit-001",
        },
    )
    assert create_response.status_code == 201

    audit_response = client.get("/audit-log")
    assert audit_response.status_code == 200
    records = audit_response.json()
    event_types = {record["event_type"] for record in records}

    assert "transfer_created" in event_types
    assert "transfer_decision" in event_types
