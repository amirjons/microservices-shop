from sqlalchemy import Column, Integer, String, Float, Enum, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

# Базовый класс для всех моделей SQLAlchemy
Base = declarative_base()


# Перечисление возможных статусов заказа
class OrderStatus(str, enum.Enum):
    NEW = "NEW"
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"


# Модель таблицы заказов
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # ID пользователя, сделавшего заказ
    amount = Column(Float, nullable=False)  # Сумма заказа
    description = Column(String, nullable=True)  # Описание товара

    # Статус заказа
    status = Column(Enum(OrderStatus), default=OrderStatus.NEW)

    # Время создания
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Время последнего обновления
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Модель для паттерна Transactional Outbox (Техническая таблица)
class OutboxMessage(Base):
    __tablename__ = "outbox_messages"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)  # Тип события
    event_data = Column(String, nullable=False)  # Данные события в формате JSON
    processed = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)  # Когда сообщение было отправлено в RabbitMQ