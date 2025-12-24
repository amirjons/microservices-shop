from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AccountCreate(BaseModel):
    pass


# Валидация входных данных: сумма пополнения должна быть строго больше нуля
class AccountTopUp(BaseModel):
    amount: float = Field(gt=0, description="Amount must be positive")


# Схема для сериализации ответа клиенту с текущим состоянием счета
class AccountResponse(BaseModel):
    id: int
    user_id: int
    balance: float
    created_at: datetime

    # Конфигурация, позволяющая Pydantic читать данные напрямую из объектов ORM
    class Config:
        from_attributes = True


# Модель данных для запроса на списание средств
class PaymentRequest(BaseModel):
    order_id: int
    user_id: int
    amount: float
    description: Optional[str] = None


# Структура события с результатом транзакции для отправки обратно в сервис заказов
class PaymentResult(BaseModel):
    transaction_id: str
    order_id: int
    user_id: int
    success: bool
    message: Optional[str] = None
    remaining_balance: Optional[float] = None