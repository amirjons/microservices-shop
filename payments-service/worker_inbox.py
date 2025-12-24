import asyncio
import json
import aio_pika
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, and_
from models import InboxMessage, Account, ProcessedTransaction, OutboxMessage
import os
import uuid
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")


async def process_inbox():
    logger.info("Payment processor started...")
    engine = create_engine(DATABASE_URL)

    while True:
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            async with connection:
                channel = await connection.channel()
                orders_queue = await channel.declare_queue("orders.to_pay", durable=True)

                async for message in orders_queue:
                    async with message.process():
                        try:
                            data = json.loads(message.body.decode())
                            # Генерируем ID для дедупликации
                            msg_id_str = f"{data['order_id']}_{data['timestamp']}"
                            message_id = str(uuid.uuid5(uuid.NAMESPACE_OID, msg_id_str))

                            with Session(engine) as session:
                                # Идемпотентность: проверяем, было ли сообщение
                                existing = session.query(InboxMessage).filter(
                                    InboxMessage.message_id == message_id
                                ).first()

                                if existing:
                                    logger.info(f"Message {message_id} already processed")
                                    continue

                                # Сохраняем в Inbox
                                inbox_msg = InboxMessage(
                                    message_id=message_id,
                                    event_type="order_created",
                                    event_data=message.body.decode()
                                )
                                session.add(inbox_msg)
                                session.flush()

                                # ЛОГИКА ОПЛАТЫ
                                result = process_payment_logic(session, data, message_id)

                                # Сохраняем ответ в Outbox
                                outbox_msg = OutboxMessage(
                                    event_type="payment_result",
                                    event_data=json.dumps(result)
                                )
                                session.add(outbox_msg)

                                inbox_msg.processed = True
                                inbox_msg.processed_at = datetime.now()
                                session.commit()
                                logger.info(f"Processed order #{data['order_id']}. Success: {result['success']}")

                        except Exception as e:
                            logger.error(f"Error processing payment: {e}")

        except Exception as e:
            logger.error(f"Connection error in payment processor: {e}")
            await asyncio.sleep(5)


def process_payment_logic(session: Session, data: dict, message_id: str) -> dict:
    order_id = data["order_id"]
    user_id = data["user_id"]
    amount = data["amount"]

    transaction_id = str(uuid.uuid5(uuid.NAMESPACE_OID, f"{order_id}_{message_id}_tx"))

    # Блокируем счет для обновления
    account = session.query(Account).filter(
        Account.user_id == user_id
    ).with_for_update().first()

    # СЦЕНАРИЙ: СЧЕТА НЕТ
    if not account:
        return {
            "transaction_id": transaction_id,
            "order_id": order_id,
            "user_id": user_id,
            "success": False,  # ОПЛАТА НЕ ПРОШЛА
            "message": "Account not found"
        }

    # СЦЕНАРИЙ: МАЛО ДЕНЕГ
    if account.balance < amount:
        return {
            "transaction_id": transaction_id,
            "order_id": order_id,
            "user_id": user_id,
            "success": False,  # ОПЛАТА НЕ ПРОШЛА
            "message": "Insufficient funds"
        }

    # СЦЕНАРИЙ: УСПЕХ
    account.balance -= amount

    # Сохраняем транзакцию для истории
    tx = ProcessedTransaction(
        transaction_id=transaction_id,
        order_id=order_id,
        user_id=user_id,
        amount=amount,
        status="SUCCESS"
    )
    session.add(tx)

    return {
        "transaction_id": transaction_id,
        "order_id": order_id,
        "user_id": user_id,
        "success": True,  # УСПЕХ!
        "message": "Payment successful",
        "remaining_balance": account.balance
    }


if __name__ == "__main__":
    asyncio.run(process_inbox())