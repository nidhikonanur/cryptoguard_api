from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.schemas import OrderCreate, RiskAssessment, TransferCreate


SUPPORTED_ASSETS = {"BTC", "ETH", "SOL"}
SUPPORTED_SYMBOLS = {"BTC-USD", "ETH-USD", "SOL-USD"}
HIGH_RISK_SYMBOLS = {"SOL-USD"}


@dataclass(slots=True)
class AccountActivitySnapshot:
    transfer_count: int = 0
    order_count: int = 0

    @property
    def total(self) -> int:
        return self.transfer_count + self.order_count


def _decision_for_score(score: int, hard_reject: bool = False) -> str:
    if hard_reject or score >= 80:
        return "rejected"
    if score >= 40:
        return "flagged"
    return "approved"


def _dedupe_reasons(reasons: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for reason in reasons:
        if reason not in seen:
            seen.add(reason)
            deduped.append(reason)
    return deduped


def score_transfer(
    payload: TransferCreate,
    activity: AccountActivitySnapshot,
) -> RiskAssessment:
    score = 0
    reasons: list[str] = []
    hard_reject = False

    if payload.asset_symbol not in SUPPORTED_ASSETS:
        score += 100
        hard_reject = True
        reasons.append("unsupported asset")

    if payload.amount >= 100_000:
        score += 55
        reasons.append("very large transfer amount")
    elif payload.amount >= 25_000:
        score += 30
        reasons.append("large transfer amount")

    address = payload.destination_address
    if len(address) < 12:
        score += 45
        reasons.append("destination address is suspiciously short")
    if not address.startswith(("0x", "bc1", "sol")):
        score += 20
        reasons.append("destination address format is unusual")

    if not payload.memo:
        score += 10
        reasons.append("missing memo")

    if activity.total >= 5:
        score += 25
        reasons.append("repeated account activity")
    elif activity.total >= 3:
        score += 10
        reasons.append("elevated recent account activity")

    final_reasons = _dedupe_reasons(reasons)
    return RiskAssessment(
        score=score,
        decision=_decision_for_score(score, hard_reject=hard_reject),
        reasons=final_reasons or ["passed baseline transfer checks"],
    )


def score_order(
    payload: OrderCreate,
    activity: AccountActivitySnapshot,
) -> RiskAssessment:
    score = 0
    reasons: list[str] = []
    hard_reject = False

    if payload.symbol not in SUPPORTED_SYMBOLS:
        score += 100
        hard_reject = True
        reasons.append("unsupported symbol")

    notional = payload.quantity * payload.limit_price
    if notional >= 250_000:
        score += 55
        reasons.append("unusually large order notional")
    elif notional >= 50_000:
        score += 25
        reasons.append("large order notional")

    if payload.symbol in HIGH_RISK_SYMBOLS:
        score += 15
        reasons.append("symbol is configured as high risk")

    if payload.quantity >= 100:
        score += 15
        reasons.append("large order quantity")

    if activity.total >= 5:
        score += 20
        reasons.append("repeated account activity")
    elif activity.total >= 3:
        score += 10
        reasons.append("elevated recent account activity")

    final_reasons = _dedupe_reasons(reasons)
    return RiskAssessment(
        score=score,
        decision=_decision_for_score(score, hard_reject=hard_reject),
        reasons=final_reasons or ["passed baseline order checks"],
    )
