from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.generations import (
    get_or_create_balance,
    purchase_plan,
    PACKAGE_CREDITS,
    SUBSCRIPTION_CREDITS,
)


router = APIRouter(prefix="/billing", tags=["billing"])


class BalanceResponse(BaseModel):
    email: str
    remaining_std: int
    used_std: int
    remaining_hd: int
    used_hd: int
    current_plan: str
    package_plan_id: Optional[str]
    purchased_at: Optional[datetime]
    plan_expires_at: Optional[datetime]


class PurchaseRequest(BaseModel):
    plan_id: str


class PurchaseResponse(BaseModel):
    email: str
    remaining_std: int
    used_std: int
    remaining_hd: int
    used_hd: int
    current_plan: str
    package_plan_id: Optional[str]
    purchased_at: Optional[datetime]
    plan_expires_at: Optional[datetime]
    added_std: int
    added_hd: int


@router.get("/balance", response_model=BalanceResponse)
def get_balance(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> BalanceResponse:
    balance = get_or_create_balance(db, current_user)
    return BalanceResponse(
        email=balance.email,
        remaining_std=balance.remaining_std,
        used_std=balance.used_std,
        remaining_hd=balance.remaining_hd,
        used_hd=balance.used_hd,
        current_plan=balance.current_plan,
        package_plan_id=balance.package_plan_id,
        purchased_at=balance.purchased_at,
        plan_expires_at=balance.plan_expires_at,
    )


@router.post("/purchase", response_model=PurchaseResponse)
def purchase(
    payload: PurchaseRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PurchaseResponse:
    plan_id = payload.plan_id.lower()
    result = purchase_plan(db, current_user, plan_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неизвестный план или пакет",
        )
    balance, added_std, added_hd = result
    return PurchaseResponse(
        email=balance.email,
        remaining_std=balance.remaining_std,
        used_std=balance.used_std,
        remaining_hd=balance.remaining_hd,
        used_hd=balance.used_hd,
        current_plan=balance.current_plan,
        package_plan_id=balance.package_plan_id,
        purchased_at=balance.purchased_at,
        plan_expires_at=balance.plan_expires_at,
        added_std=added_std,
        added_hd=added_hd,
    )

