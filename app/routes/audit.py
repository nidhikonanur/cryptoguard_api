from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import AuditLogResponse
from app.services import CryptoGuardService


router = APIRouter(prefix="/audit-log", tags=["audit"])


@router.get("", response_model=list[AuditLogResponse])
def list_audit_log(session: Session = Depends(get_session)) -> list[AuditLogResponse]:
    service = CryptoGuardService(session)
    return [AuditLogResponse.model_validate(record) for record in service.list_audit_logs()]
