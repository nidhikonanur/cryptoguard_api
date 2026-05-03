from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Decision = Literal["approved", "flagged", "rejected"]
TransferStatus = Literal["approved", "flagged", "rejected"]
OrderStatus = Literal["approved", "flagged", "rejected"]
OrderSide = Literal["buy", "sell"]


class TransferCreate(BaseModel):
    sender_account_id: str = Field(..., min_length=3, max_length=64)
    destination_address: str = Field(..., min_length=4, max_length=255)
    asset_symbol: str = Field(..., min_length=2, max_length=16)
    amount: float = Field(..., gt=0)
    memo: str | None = Field(default=None, max_length=255)
    idempotency_key: str = Field(..., min_length=8, max_length=128)

    @field_validator("asset_symbol")
    @classmethod
    def normalize_asset_symbol(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("destination_address")
    @classmethod
    def strip_address(cls, value: str) -> str:
        return value.strip()

    @field_validator("memo")
    @classmethod
    def normalize_memo(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None


class TransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_account_id: str
    destination_address: str
    asset_symbol: str
    amount: float
    memo: str | None
    idempotency_key: str
    status: TransferStatus
    risk_score: int
    risk_reasons: list[str]
    created_at: datetime
    idempotent_replay: bool = False


class OrderCreate(BaseModel):
    account_id: str = Field(..., min_length=3, max_length=64)
    symbol: str = Field(..., min_length=3, max_length=32)
    side: OrderSide
    quantity: float = Field(..., gt=0)
    limit_price: float = Field(..., gt=0)
    idempotency_key: str = Field(..., min_length=8, max_length=128)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("side")
    @classmethod
    def normalize_side(cls, value: str) -> str:
        return value.strip().lower()


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: str
    symbol: str
    side: OrderSide
    quantity: float
    limit_price: float
    idempotency_key: str
    status: OrderStatus
    risk_score: int
    risk_reasons: list[str]
    created_at: datetime
    idempotent_replay: bool = False


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    event_type: str
    entity_type: str
    entity_id: int
    decision: str | None
    risk_score: int | None
    reason_summary: str | None


class HealthResponse(BaseModel):
    status: str
    database: str


class RiskAssessment(BaseModel):
    score: int
    decision: Decision
    reasons: list[str]
