from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, UniqueConstraint, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


# Модель счета пользователя.
class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    balance = Column(Float, nullable=False, default=0.0)

    # Поле версии для реализации Optimistic Locking
    version = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # баланс не может быть меньше нуля
    __table_args__ = (
        CheckConstraint('balance >= 0', name='balance_non_negative'),
    )


# Таблица для паттерна Transactional Inbox (Входящие сообщения)
class InboxMessage(Base):
    __tablename__ = "inbox_messages"

    id = Column(Integer, primary_key=True, index=True)

    # Уникальный ID сообщения
    message_id = Column(String, nullable=False, unique=True, index=True)

    event_type = Column(String, nullable=False)
    event_data = Column(String, nullable=False)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)


# Таблица для паттерна Transactional Outbox (Исходящие сообщения)
class OutboxMessage(Base):
    __tablename__ = "outbox_messages"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)

    # Данные события (JSON)
    event_data = Column(String, nullable=False)

    # Флаг, показывающий, было ли сообщение успешно передано в брокер
    processed = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)


# Журнал обработанных транзакций для аудита и истории
class ProcessedTransaction(Base):
    __tablename__ = "processed_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, nullable=False, unique=True, index=True)
    order_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)

    # Статус операции
    status = Column(String, nullable=False)

    processed_at = Column(DateTime(timezone=True), server_default=func.now())