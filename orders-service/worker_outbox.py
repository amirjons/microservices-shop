import asyncio
import json
import aio_pika
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from models import OutboxMessage
import os
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройки подключения
DATABASE_URL = os.getenv("DATABASE_URL")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")


async def process_outbox():

    logger.info("Запуск воркера Outbox (отправка сообщений в RabbitMQ)...")

    # Создаем синхронный движок для работы с БД внутри цикла
    engine = create_engine(DATABASE_URL)

    while True:
        try:
            # Используем connect_robust для автоматического переподключения при разрыве связи с RabbitMQ
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            async with connection:
                channel = await connection.channel()

                # Бесконечный цикл обработки сообщений
                while True:
                    with Session(engine) as session:
                        # 1. Читаем неотправленные сообщения из таблицы outbox_messages
                        # Берем пачками по 50 штук, чтобы не забивать память
                        messages = session.query(OutboxMessage).filter(
                            OutboxMessage.processed == False
                        ).limit(50).all()

                        # Если сообщений нет, спим полсекунды и проверяем снова
                        if not messages:
                            await asyncio.sleep(0.5)
                            continue

                        for message in messages:
                            try:
                                # 2. Отправляем сообщение в очередь 'orders.to_pay'
                                await channel.default_exchange.publish(
                                    aio_pika.Message(
                                        body=message.event_data.encode(),
                                        content_type="application/json",
                                        # PERSISTENT означает, что сообщение сохранится на диске брокера
                                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                                    ),
                                    routing_key="orders.to_pay"
                                )

                                # 3. Помечаем сообщение как обработанное в БД
                                message.processed = True
                                message.processed_at = datetime.now()
                                logger.info(f"Сообщение #{message.id} успешно отправлено в RabbitMQ")

                            except Exception as e:
                                logger.error(f"Не удалось отправить сообщение #{message.id}: {e}")

                        # 4. Фиксируем изменения в БД
                        session.commit()

                    # Небольшая пауза между пачками, чтобы не грузить CPU в холостую
                    await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Ошибка подключения к RabbitMQ в Outbox воркере: {e}")
            # Если брокер упал, ждем 5 секунд перед попыткой переподключения
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(process_outbox())