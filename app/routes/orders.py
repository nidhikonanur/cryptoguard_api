from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import OrderCreate, OrderResponse
from app.services import CryptoGuardService, to_order_response


router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    response: Response,
    session: Session = Depends(get_session),
) -> OrderResponse:
    service = CryptoGuardService(session)
    result = service.create_order(payload)
    if result.idempotent_replay:
        response.status_code = status.HTTP_200_OK
    return to_order_response(result.entity, idempotent_replay=result.idempotent_replay)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, session: Session = Depends(get_session)) -> OrderResponse:
    service = CryptoGuardService(session)
    order = service.get_order(order_id)
    return to_order_response(order)
