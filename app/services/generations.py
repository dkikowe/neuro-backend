from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models.generation import GenerationBalance
from app.models.user import User


# Количество начислений по пакетам (mock): (std, hd)
PACKAGE_CREDITS: dict[str, Tuple[int, int]] = {
    "hd_1": (1, 1),
    "hd_3": (3, 3),
    "hd_5": (5, 5),
    "hd_10": (10, 10),
    "hd_20": (20, 20),
}

# Подписки (mock значения для зачисления): (std, hd)
SUBSCRIPTION_CREDITS: dict[str, Tuple[int, int]] = {
    "lite": (30, 10),
    "standard": (100, 40),
    "pro": (300, 150),
}


def _refresh_if_expired(balance: GenerationBalance) -> None:
    if balance.plan_expires_at and balance.plan_expires_at < datetime.utcnow():
        # Сброс до бесплатного плана
        balance.remaining_std = 1
        balance.used_std = 0
        balance.remaining_hd = 0
        balance.used_hd = 0
        balance.current_plan = "free"
        balance.plan_expires_at = None
        balance.purchased_at = datetime.utcnow()


def get_or_create_balance(db: Session, user: User) -> GenerationBalance:
    balance = (
        db.query(GenerationBalance)
        .filter(GenerationBalance.user_id == user.id)
        .first()
    )
    if balance:
        _refresh_if_expired(balance)
        db.add(balance)
        db.commit()
        db.refresh(balance)
        return balance
    balance = GenerationBalance(
        user_id=user.id,
        email=user.email,
        remaining_std=1,  # одна бесплатная стандартная генерация
        used_std=0,
        remaining_hd=0,
        used_hd=0,
        current_plan="free",
        purchased_at=datetime.utcnow(),
        plan_expires_at=None,
    )
    db.add(balance)
    db.commit()
    db.refresh(balance)
    return balance


def consume_generation(db: Session, user: User, is_hd: bool = False) -> GenerationBalance:
    balance = get_or_create_balance(db, user)
    _refresh_if_expired(balance)
    if is_hd:
        if balance.remaining_hd <= 0:
            raise ValueError("Лимит HD-генераций исчерпан")
        balance.remaining_hd -= 1
        balance.used_hd += 1
    else:
        if balance.remaining_std <= 0:
            raise ValueError("Лимит генераций исчерпан")
        balance.remaining_std -= 1
        balance.used_std += 1
    db.add(balance)
    db.commit()
    db.refresh(balance)
    return balance


def add_credits(db: Session, user: User, credits_std: int, credits_hd: int, plan: str) -> GenerationBalance:
    balance = get_or_create_balance(db, user)
    balance.remaining_std += credits_std
    balance.remaining_hd += credits_hd
    balance.current_plan = plan
    balance.purchased_at = datetime.utcnow()
    db.add(balance)
    db.commit()
    db.refresh(balance)
    return balance


def purchase_plan(db: Session, user: User, plan_id: str) -> Optional[Tuple[GenerationBalance, int, int]]:
    plan_id = plan_id.lower()
    credits: Optional[Tuple[int, int]] = None
    if plan_id in PACKAGE_CREDITS:
        credits = PACKAGE_CREDITS[plan_id]
    elif plan_id in SUBSCRIPTION_CREDITS:
        credits = SUBSCRIPTION_CREDITS[plan_id]

    if not credits:
        return None

    balance = get_or_create_balance(db, user)

    if plan_id in SUBSCRIPTION_CREDITS:
        # Подписки: ежемесячный пакет, сбрасываем счётчики и устанавливаем срок
        balance.remaining_std = credits[0]
        balance.used_std = 0
        balance.remaining_hd = credits[1]
        balance.used_hd = 0
        balance.current_plan = plan_id
        balance.purchased_at = datetime.utcnow()
        balance.plan_expires_at = datetime.utcnow() + timedelta(days=30)
    else:
        # Разовые пакеты: просто добавляем к балансу (без срока)
        balance.remaining_std += credits[0]
        balance.remaining_hd += credits[1]
        balance.current_plan = plan_id
        balance.purchased_at = datetime.utcnow()

    db.add(balance)
    db.commit()
    db.refresh(balance)
    return balance, credits[0], credits[1]

