import asyncio
import json
import aio_pika
import redis.asyncio as aioredis
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from models import Order, OrderStatus
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


async def process_payment_results():
    logger.info("Inbox worker started...")
    engine = create_engine(DATABASE_URL)

    # Подключение к Redis для уведомлений
    redis_client = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

    while True:
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            async with connection:
                channel = await connection.channel()
                results_queue = await channel.declare_queue("payment.results", durable=True)

                async for message in results_queue:
                    async with message.process():
                        try:
                            data = json.loads(message.body.decode())
                            logger.info(f"Received result for Order #{data.get('order_id')}: {data.get('success')}")

                            with Session(engine) as session:
                                order = session.query(Order).filter(
                                    Order.id == data["order_id"]
                                ).first()

                                if order:
                                    # Обновляем статус
                                    if data["success"]:
                                        order.status = OrderStatus.FINISHED
                                    else:
                                        order.status = OrderStatus.CANCELLED

                                    session.commit()

                                    # Отправляем уведомление в Redis для фронтенда
                                    notification = {
                                        "type": "order_update",
                                        "order_id": order.id,
                                        "user_id": order.user_id,
                                        "status": order.status.value,
                                        "amount": order.amount,
                                        "message": f"Статус заказа #{order.id} изменен на: {order.status.value}"
                                    }
                                    await redis_client.publish("order_updates", json.dumps(notification))
                                    logger.info(f"Updated Order #{order.id} to {order.status}")

                        except Exception as e:
                            logger.error(f"Error processing message: {e}")

        except Exception as e:
            logger.error(f"Connection error in inbox worker: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(process_payment_results())