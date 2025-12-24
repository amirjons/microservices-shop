from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


# Перечисление статусов заказа для строгой типизации
class OrderStatus(str, Enum):
    NEW = "NEW"
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"


# Схема данных для создания заказа
class OrderCreate(BaseModel):
    amount: float           # Сумма заказа
    description: Optional[str] = None


# Схема данных для ответа API
class OrderResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    description: Optional[str]
    status: OrderStatus
    created_at: datetime

    class Config:
        from_attributes = True


# Схема сообщения с результатом оплаты
# Используется при чтении сообщений из RabbitMQ от сервиса платежей
class PaymentResult(BaseModel):
    order_id: int
    user_id: int
    success: bool
    message: Optional[str] = None
    transaction_id: Optional[str] = None