from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import TransferCreate, TransferResponse
from app.services import CryptoGuardService, to_transfer_response


router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
def create_transfer(
    payload: TransferCreate,
    response: Response,
    session: Session = Depends(get_session),
) -> TransferResponse:
    service = CryptoGuardService(session)
    result = service.create_transfer(payload)
    if result.idempotent_replay:
        response.status_code = status.HTTP_200_OK
    return to_transfer_response(result.entity, idempotent_replay=result.idempotent_replay)


@router.get("/{transfer_id}", response_model=TransferResponse)
def get_transfer(transfer_id: int, session: Session = Depends(get_session)) -> TransferResponse:
    service = CryptoGuardService(session)
    transfer = service.get_transfer(transfer_id)
    return to_transfer_response(transfer)
