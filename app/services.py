from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, IdempotencyRecord, Order, Transfer
from app.risk import AccountActivitySnapshot, score_order, score_transfer
from app.schemas import OrderCreate, OrderResponse, TransferCreate, TransferResponse


def _hash_payload(payload: dict) -> str:
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def _serialize_reasons(reasons: list[str]) -> str:
    return json.dumps(reasons)


def _deserialize_reasons(reasons: str) -> list[str]:
    return json.loads(reasons)


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def write(
        self,
        *,
        event_type: str,
        entity_type: str,
        entity_id: int,
        decision: str | None,
        risk_score: int | None,
        reason_summary: str | None,
    ) -> AuditLog:
        record = AuditLog(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            decision=decision,
            risk_score=risk_score,
            reason_summary=reason_summary,
        )
        self.session.add(record)
        return record

    def list_all(self) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc(), AuditLog.id.desc())
        return list(self.session.scalars(stmt))


class TransferRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: TransferCreate, *, risk_score: int, decision: str, reasons: list[str]) -> Transfer:
        transfer = Transfer(
            sender_account_id=payload.sender_account_id,
            destination_address=payload.destination_address,
            asset_symbol=payload.asset_symbol,
            amount=payload.amount,
            memo=payload.memo,
            idempotency_key=payload.idempotency_key,
            status=decision,
            risk_score=risk_score,
            risk_reasons=_serialize_reasons(reasons),
        )
        self.session.add(transfer)
        self.session.flush()
        return transfer

    def get(self, transfer_id: int) -> Transfer | None:
        return self.session.get(Transfer, transfer_id)

    def count_for_account(self, account_id: str) -> int:
        stmt = select(Transfer).where(Transfer.sender_account_id == account_id)
        return len(list(self.session.scalars(stmt)))


class OrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: OrderCreate, *, risk_score: int, decision: str, reasons: list[str]) -> Order:
        order = Order(
            account_id=payload.account_id,
            symbol=payload.symbol,
            side=payload.side,
            quantity=payload.quantity,
            limit_price=payload.limit_price,
            idempotency_key=payload.idempotency_key,
            status=decision,
            risk_score=risk_score,
            risk_reasons=_serialize_reasons(reasons),
        )
        self.session.add(order)
        self.session.flush()
        return order

    def get(self, order_id: int) -> Order | None:
        return self.session.get(Order, order_id)

    def count_for_account(self, account_id: str) -> int:
        stmt = select(Order).where(Order.account_id == account_id)
        return len(list(self.session.scalars(stmt)))


class IdempotencyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, *, entity_type: str, key: str) -> IdempotencyRecord | None:
        stmt = select(IdempotencyRecord).where(
            IdempotencyRecord.entity_type == entity_type,
            IdempotencyRecord.idempotency_key == key,
        )
        return self.session.scalar(stmt)

    def create(self, *, entity_type: str, key: str, request_hash: str, entity_id: int) -> IdempotencyRecord:
        record = IdempotencyRecord(
            entity_type=entity_type,
            idempotency_key=key,
            request_hash=request_hash,
            entity_id=entity_id,
        )
        self.session.add(record)
        return record


@dataclass(slots=True)
class CreateResult[T]:
    entity: T
    idempotent_replay: bool


class CryptoGuardService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.transfers = TransferRepository(session)
        self.orders = OrderRepository(session)
        self.audit = AuditRepository(session)
        self.idempotency = IdempotencyRepository(session)

    def _activity_snapshot(self, account_id: str) -> AccountActivitySnapshot:
        return AccountActivitySnapshot(
            transfer_count=self.transfers.count_for_account(account_id),
            order_count=self.orders.count_for_account(account_id),
        )

    def create_transfer(self, payload: TransferCreate) -> CreateResult[Transfer]:
        request_hash = _hash_payload(payload.model_dump())
        existing = self.idempotency.get(entity_type="transfer", key=payload.idempotency_key)
        if existing:
            if existing.request_hash != request_hash:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key has already been used with a different transfer payload.",
                )
            entity = self.transfers.get(existing.entity_id)
            if entity is None:
                raise HTTPException(status_code=500, detail="Idempotency record points to a missing transfer.")
            self.audit.write(
                event_type="transfer_idempotency_replay",
                entity_type="transfer",
                entity_id=entity.id,
                decision=entity.status,
                risk_score=entity.risk_score,
                reason_summary="replayed original transfer response",
            )
            self.session.commit()
            return CreateResult(entity=entity, idempotent_replay=True)

        assessment = score_transfer(payload, self._activity_snapshot(payload.sender_account_id))
        transfer = self.transfers.create(
            payload,
            risk_score=assessment.score,
            decision=assessment.decision,
            reasons=assessment.reasons,
        )
        self.idempotency.create(
            entity_type="transfer",
            key=payload.idempotency_key,
            request_hash=request_hash,
            entity_id=transfer.id,
        )
        self.audit.write(
            event_type="transfer_created",
            entity_type="transfer",
            entity_id=transfer.id,
            decision=None,
            risk_score=None,
            reason_summary=f"created transfer for {payload.asset_symbol}",
        )
        self.audit.write(
            event_type="transfer_decision",
            entity_type="transfer",
            entity_id=transfer.id,
            decision=assessment.decision,
            risk_score=assessment.score,
            reason_summary=", ".join(assessment.reasons),
        )
        self.session.commit()
        self.session.refresh(transfer)
        return CreateResult(entity=transfer, idempotent_replay=False)

    def get_transfer(self, transfer_id: int) -> Transfer:
        transfer = self.transfers.get(transfer_id)
        if transfer is None:
            raise HTTPException(status_code=404, detail="Transfer not found.")
        return transfer

    def create_order(self, payload: OrderCreate) -> CreateResult[Order]:
        request_hash = _hash_payload(payload.model_dump())
        existing = self.idempotency.get(entity_type="order", key=payload.idempotency_key)
        if existing:
            if existing.request_hash != request_hash:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key has already been used with a different order payload.",
                )
            entity = self.orders.get(existing.entity_id)
            if entity is None:
                raise HTTPException(status_code=500, detail="Idempotency record points to a missing order.")
            self.audit.write(
                event_type="order_idempotency_replay",
                entity_type="order",
                entity_id=entity.id,
                decision=entity.status,
                risk_score=entity.risk_score,
                reason_summary="replayed original order response",
            )
            self.session.commit()
            return CreateResult(entity=entity, idempotent_replay=True)

        assessment = score_order(payload, self._activity_snapshot(payload.account_id))
        order = self.orders.create(
            payload,
            risk_score=assessment.score,
            decision=assessment.decision,
            reasons=assessment.reasons,
        )
        self.idempotency.create(
            entity_type="order",
            key=payload.idempotency_key,
            request_hash=request_hash,
            entity_id=order.id,
        )
        self.audit.write(
            event_type="order_created",
            entity_type="order",
            entity_id=order.id,
            decision=None,
            risk_score=None,
            reason_summary=f"created order for {payload.symbol}",
        )
        self.audit.write(
            event_type="order_decision",
            entity_type="order",
            entity_id=order.id,
            decision=assessment.decision,
            risk_score=assessment.score,
            reason_summary=", ".join(assessment.reasons),
        )
        self.session.commit()
        self.session.refresh(order)
        return CreateResult(entity=order, idempotent_replay=False)

    def get_order(self, order_id: int) -> Order:
        order = self.orders.get(order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found.")
        return order

    def list_audit_logs(self) -> list[AuditLog]:
        return self.audit.list_all()


def to_transfer_response(transfer: Transfer, *, idempotent_replay: bool = False) -> TransferResponse:
    return TransferResponse(
        id=transfer.id,
        sender_account_id=transfer.sender_account_id,
        destination_address=transfer.destination_address,
        asset_symbol=transfer.asset_symbol,
        amount=transfer.amount,
        memo=transfer.memo,
        idempotency_key=transfer.idempotency_key,
        status=transfer.status,
        risk_score=transfer.risk_score,
        risk_reasons=_deserialize_reasons(transfer.risk_reasons),
        created_at=transfer.created_at,
        idempotent_replay=idempotent_replay,
    )


def to_order_response(order: Order, *, idempotent_replay: bool = False) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        account_id=order.account_id,
        symbol=order.symbol,
        side=order.side,
        quantity=order.quantity,
        limit_price=order.limit_price,
        idempotency_key=order.idempotency_key,
        status=order.status,
        risk_score=order.risk_score,
        risk_reasons=_deserialize_reasons(order.risk_reasons),
        created_at=order.created_at,
        idempotent_replay=idempotent_replay,
    )
