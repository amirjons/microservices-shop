import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket
from contextlib import asynccontextmanager
import redis.asyncio as aioredis
import os

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = None
        self.pubsub = None
        self.instance_id = os.getenv("INSTANCE_ID", "1")

    async def connect_redis(self):
        """Подключение к Redis для pub/sub"""
        try:
            self.redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
            self.pubsub = self.redis_client.pubsub()
            # Подписываемся на канал обновлений заказов
            await self.pubsub.subscribe("order_updates")
            logger.info(f"Instance {self.instance_id} connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")

    async def disconnect_redis(self):
        """Отключение от Redis"""
        if self.pubsub:
            await self.pubsub.unsubscribe("order_updates")
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()

    async def connect(self, websocket: WebSocket, user_id: int):
        """Подключение клиента по WebSocket"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected to WebSocket on instance {self.instance_id}")

    async def disconnect(self, websocket: WebSocket, user_id: int):
        """Отключение клиента"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected from WebSocket")

    async def send_personal_message(self, message: dict, user_id: int):
        """Отправка сообщения конкретному пользователю"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")

    async def broadcast_order_update(self, order_id: int, user_id: int, status: str, amount: float = None):
        """Отправка обновления статуса заказа всем подключенным клиентам пользователя"""
        message = {
            "type": "order_update",
            "order_id": order_id,
            "user_id": user_id,
            "status": status,
            "amount": amount,
            "timestamp": asyncio.get_event_loop().time(),
            "message": f"Статус заказа #{order_id} изменен на: {status}"
        }

        # Отправляем локально подключенным клиентам
        await self.send_personal_message(message, user_id)

        # Публикуем в Redis для других инстансов
        if self.redis_client:
            try:
                await self.redis_client.publish("order_updates", json.dumps(message))
                logger.info(f"Order update published to Redis: {order_id} -> {status}")
            except Exception as e:
                logger.error(f"Failed to publish to Redis: {e}")

    async def listen_to_redis(self):
        """Прослушивание сообщений из Redis"""
        if not self.pubsub:
            return

        logger.info(f"Instance {self.instance_id} started listening to Redis")

        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        if data["type"] == "order_update":
                            user_id = data["user_id"]
                            # Отправляем сообщение всем локально подключенным клиентам этого пользователя
                            await self.send_personal_message(data, user_id)
                            logger.info(f"Redis message forwarded to user {user_id}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON from Redis: {e}")
        except Exception as e:
            logger.error(f"Redis listener error: {e}")


# Создаём глобальный экземпляр менеджера
ws_manager = WebSocketManager()


@asynccontextmanager
async def websocket_lifespan(app):
    """Lifespan для управления WebSocket соединениями"""
    # Startup
    logger.info("Starting WebSocket manager...")
    await ws_manager.connect_redis()
    # Запускаем слушателя Redis в фоне
    asyncio.create_task(ws_manager.listen_to_redis())

    yield

    # Shutdown
    logger.info("Shutting down WebSocket manager...")
    await ws_manager.disconnect_redis()