import hashlib
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from urllib.parse import urlencode
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Form, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models.payment import Payment
from app.services.generations import purchase_plan
from app.models.user import User


router = APIRouter(prefix="/robokassa", tags=["robokassa"])

settings = get_settings()


def _format_amount(amount: float) -> str:
    # Безопасное округление суммы до 2 знаков
    quantized = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    # Robokassa ожидает точку как разделитель
    return format(quantized, "f")


def _md5(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


class CreatePaymentRequest(BaseModel):
    order_id: int = Field(..., description="ID заказа (InvId)")
    amount: float = Field(..., description="Сумма платежа")
    description: str = Field(..., description="Описание платежа")
    plan_id: Optional[str] = Field(None, description="План/пакет, который покупает пользователь")


class CreatePaymentResponse(BaseModel):
    payment_url: str


@router.post("/create-payment", response_model=CreatePaymentResponse)
def create_payment(
    payload: CreatePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreatePaymentResponse:
    if not settings.ROBOKASSA_LOGIN or not settings.ROBOKASSA_PASSWORD_1:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Robokassa не настроена",
        )

    out_sum = _format_amount(payload.amount)
    inv_id = payload.order_id

    # Регистрируем платёж (pending)
    payment = (
        db.query(Payment)
        .filter(Payment.inv_id == inv_id, Payment.user_id == current_user.id)
        .first()
    )
    if not payment:
        payment = Payment(
            inv_id=inv_id,
            user_id=current_user.id,
            plan_id=payload.plan_id,
            amount=Decimal(out_sum),
            description=payload.description,
            status="pending",
        )
        db.add(payment)
    else:
        payment.plan_id = payload.plan_id
        payment.amount = Decimal(out_sum)
        payment.description = payload.description
        payment.status = "pending"
    db.commit()
    db.refresh(payment)

    signature_str = f"{settings.ROBOKASSA_LOGIN}:{out_sum}:{inv_id}:{settings.ROBOKASSA_PASSWORD_1}"
    signature = _md5(signature_str)

    params = {
        "MerchantLogin": settings.ROBOKASSA_LOGIN,
        "OutSum": out_sum,
        "InvId": inv_id,
        "Description": payload.description,
        "SignatureValue": signature,
    }
    if settings.ROBOKASSA_IS_TEST:
        params["IsTest"] = 1

    payment_url = f"https://auth.robokassa.ru/Merchant/Index.aspx?{urlencode(params)}"
    return CreatePaymentResponse(payment_url=payment_url)


@router.post("/result")
def result_callback(
    out_sum_form: Optional[str] = Form(None),
    inv_id_form: Optional[str] = Form(None),
    signature_form: Optional[str] = Form(None),
    out_sum_q: Optional[str] = Query(None),
    inv_id_q: Optional[str] = Query(None),
    signature_q: Optional[str] = Query(None),
):
    if not settings.ROBOKASSA_PASSWORD_2:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Robokassa не настроена",
        )

    out_sum = out_sum_form or out_sum_q
    inv_id = inv_id_form or inv_id_q
    signature = signature_form or signature_q

    if not out_sum or not inv_id or not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Отсутствуют необходимые параметры",
        )

    expected_str = f"{out_sum}:{inv_id}:{settings.ROBOKASSA_PASSWORD_2}"
    expected_sig = _md5(expected_str)

    if expected_sig.lower() != signature.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Некорректная подпись",
        )

    # Отмечаем заказ как оплаченный и начисляем план/пакет
    db: Session = next(get_db())
    try:
        payment = db.query(Payment).filter(Payment.inv_id == int(inv_id)).first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Платёж не найден",
            )
        if payment.status != "paid":
            payment.status = "paid"
            payment.paid_at = datetime.utcnow()
            db.add(payment)
            # Начисляем, если есть план_id
            if payment.plan_id:
                user = db.query(User).filter(User.id == payment.user_id).first()
                if user:
                    purchase_plan(db, user, payment.plan_id)
            db.commit()
    except HTTPException:
        db.close()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обработки результата платежа: {exc}",
        )
    finally:
        db.close()

    return f"OK{inv_id}"

