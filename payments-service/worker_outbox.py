import asyncio
import json
import aio_pika
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from models import OutboxMessage
import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")


async def process_outbox():
    engine = create_engine(DATABASE_URL)

    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    # Объявляем очередь для результатов оплаты
    results_queue = await channel.declare_queue("payment.results", durable=True)

    while True:
        try:
            with Session(engine) as session:
                # Берем непроцессированные сообщения
                messages = session.query(OutboxMessage).filter(
                    OutboxMessage.processed == False
                ).limit(100).all()

                for message in messages:
                    # Отправляем в RabbitMQ
                    await channel.default_exchange.publish(
                        aio_pika.Message(
                            body=message.event_data.encode(),
                            content_type="application/json",
                            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                        ),
                        routing_key="payment.results"
                    )

                    # Помечаем как обработанное
                    message.processed = True
                    message.processed_at = datetime.now()

                session.commit()

        except Exception as e:
            print(f"Error processing outbox: {e}")

        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(process_outbox())