from fastapi import FastAPI, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import asyncio
import logging

from database import get_db
from models import Account
from schemas import AccountTopUp, AccountResponse

# Настройка логирования для отслеживания операций
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="💰 Payments Service", version="1.0.0")


# 1. Эмуляция аутентификации: извлекаем ID пользователя из заголовка запроса.
async def verify_user_id(x_user_id: int = Header(..., alias="X-User-ID")):
    if x_user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid User ID")
    return x_user_id


@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """
    2. Эндпоинт для проверки работоспособности сервиса.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/accounts", response_model=AccountResponse, status_code=201)
async def create_account(user_id: int = Depends(verify_user_id), db: Session = Depends(get_db)):
    # 3. Бизнес-правило: У одного пользователя может быть только один счет.
    existing = db.query(Account).filter(Account.user_id == user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Account already exists")

    try:
        account = Account(user_id=user_id, balance=0.0)
        db.add(account)
        # 4. Фиксируем транзакцию: сохраняем новый счет в БД.
        db.commit()
        db.refresh(account)

        # Используем метод model_validate (Pydantic v2)
        # для корректного преобразования объекта SQLAlchemy в схему ответа.
        return AccountResponse.model_validate(account)
    except Exception as e:
        # 6. В случае любой ошибки откатываем транзакцию, чтобы не было "битых" данных.
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/accounts/topup", response_model=AccountResponse)
async def topup_account(data: AccountTopUp, user_id: int = Depends(verify_user_id), db: Session = Depends(get_db)):
    try:
        # 7. Используем пессимистичную блокировку
        account = db.query(Account).filter(Account.user_id == user_id).with_for_update().first()

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        # 8. Обновляем баланс защищенным образом (внутри блокировки).
        account.balance += data.amount

        db.commit()
        db.refresh(account)
        return AccountResponse.model_validate(account)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/accounts", response_model=AccountResponse)
async def get_account(user_id: int = Depends(verify_user_id), db: Session = Depends(get_db)):
    # 9. Получение полной информации о счете текущего пользователя.
    account = db.query(Account).filter(Account.user_id == user_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountResponse.model_validate(account)


@app.get("/accounts/balance")
async def get_balance(user_id: int = Depends(verify_user_id), db: Session = Depends(get_db)):
    # 10. Упрощенный эндпоинт для получения только текущего баланса и валюты.
    account = db.query(Account).filter(Account.user_id == user_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"user_id": user_id, "balance": account.balance, "currency": "RUB"}