from fastapi import FastAPI, Request, HTTPException, Header, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
import httpx
import asyncio
from typing import Dict, Any, Optional, List
import json
import logging
from contextlib import asynccontextmanager
import redis.asyncio as aioredis
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация сервисов
SERVICE_CONFIG = {
    "orders": {
        "base_urls": ["http://orders-service-1:8000", "http://orders-service-2:8000"],
        "description": "Микросервис для управления заказами (несколько инстансов)"
    },
    "payments": {
        "base_url": "http://payments-service:8000",
        "description": "Микросервис для управления счетами и платежами"
    }
}


# Менеджер WebSocket соединений для Gateway
class GatewayWebSocketManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = None

    async def connect_redis(self):
        """Подключение к Redis для получения обновлений от сервисов"""
        try:
            self.redis_client = aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                encoding='utf-8'
            )
            logger.info("Gateway connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")

    async def disconnect_redis(self):
        """Отключение от Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Gateway disconnected from Redis")

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected to Gateway WebSocket")

    async def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected from Gateway WebSocket")

    async def send_to_user(self, user_id: int, message: dict):
        """Отправка сообщения пользователю через Gateway"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
                return True
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
        return False


# Создаем глобальный экземпляр менеджера
gateway_ws_manager = GatewayWebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events для управления ресурсами"""
    # Startup
    logger.info("Starting up API Gateway with WebSocket...")
    app.state.http_client = httpx.AsyncClient(timeout=30.0)

    # Подключаемся к Redis
    await gateway_ws_manager.connect_redis()

    # Запускаем задачу для прослушивания Redis
    if gateway_ws_manager.redis_client:
        asyncio.create_task(listen_for_order_updates())

    yield

    # Shutdown
    logger.info("Shutting down API Gateway...")
    await app.state.http_client.aclose()
    await gateway_ws_manager.disconnect_redis()


async def listen_for_order_updates():
    """Прослушивание обновлений заказов из Redis"""
    try:
        pubsub = gateway_ws_manager.redis_client.pubsub()
        await pubsub.subscribe("order_updates")

        logger.info("Gateway started listening for order updates")

        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    user_id = data.get("user_id")
                    # Пересылаем сообщение клиенту через Gateway
                    if user_id:
                        await gateway_ws_manager.send_to_user(user_id, data)
                        logger.debug(f"Order update forwarded to user {user_id}")
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from Redis: {e}")
                except Exception as e:
                    logger.error(f"Error processing Redis message: {e}")
    except Exception as e:
        logger.error(f"Redis listener error in Gateway: {e}")


# Создаем приложение FastAPI с конфигурацией Swagger
app = FastAPI(
    title="🛍️ API Gateway - Интернет-магазин 'Г ozон'",
    description="""
    ## Единая точка входа для микросервисов магазина с WebSocket поддержкой
    """,
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket endpoint в Gateway
@app.websocket("/ws/{user_id}")
async def gateway_websocket_endpoint(websocket: WebSocket, user_id: int):
    """WebSocket подключение через Gateway"""
    await gateway_ws_manager.connect(websocket, user_id)

    try:
        # Отправляем приветственное сообщение
        await websocket.send_json({
            "type": "gateway_connected",
            "message": "Connected to API Gateway WebSocket",
            "user_id": user_id,
            "timestamp": asyncio.get_event_loop().time(),
            "note": "You will receive real-time order status updates"
        })

        # Ждём сообщений от клиента
        while True:
            try:
                data = await websocket.receive_json()
                # Обработка сообщений от клиента
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": asyncio.get_event_loop().time()
                    })
            except Exception:
                break

    except WebSocketDisconnect:
        await gateway_ws_manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"Gateway WebSocket error: {e}")
        await gateway_ws_manager.disconnect(user_id)


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Проверка работоспособности API Gateway"""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": asyncio.get_event_loop().time(),
        "websocket_connections": len(gateway_ws_manager.active_connections),
        "redis_connected": gateway_ws_manager.redis_client is not None
    }


@app.get("/health/all", tags=["Health"])
async def health_all_services():
    """Проверка работоспособности всех микросервисов"""
    results = {}

    # Проверяем все инстансы Orders Service
    for i, base_url in enumerate(SERVICE_CONFIG["orders"]["base_urls"]):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}/health")
                results[f"orders_{i + 1}"] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "data": response.json() if response.content else {}
                }
        except Exception as e:
            results[f"orders_{i + 1}"] = {
                "status": "unhealthy",
                "error": str(e)
            }

    # Проверяем Payments Service
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{SERVICE_CONFIG['payments']['base_url']}/health")
            results["payments"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "data": response.json() if response.content else {}
            }
    except Exception as e:
        results["payments"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    return {
        "timestamp": asyncio.get_event_loop().time(),
        "services": results
    }


# Основной прокси-роут
@app.api_route(
    "/api/{service_name}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    tags=["Proxy"]
)
async def proxy_to_service(
        request: Request,
        service_name: str,
        path: str,
        x_user_id: Optional[int] = Header(
            None,
            alias="X-User-ID",
            description="Идентификатор пользователя",
            example=1
        )
):
    """
    Проксирует запрос к указанному микросервису.
    """
    # Для всех запросов в /api/ требуем заголовок
    if x_user_id is None:
        raise HTTPException(
            status_code=400,
            detail="Header 'X-User-ID' is required for this operation"
        )

    # Валидация service_name
    if service_name not in SERVICE_CONFIG:
        raise HTTPException(
            status_code=404,
            detail=f"Сервис '{service_name}' не найден. Доступные сервисы: {list(SERVICE_CONFIG.keys())}"
        )

    # Выбор целевого URL
    if service_name == "orders":
        # Простая round-robin балансировка
        index = x_user_id % len(SERVICE_CONFIG["orders"]["base_urls"])
        target_url = f"{SERVICE_CONFIG['orders']['base_urls'][index]}/{path.lstrip('/')}"
    else:
        config = SERVICE_CONFIG[service_name]
        target_url = f"{config['base_url']}/{path.lstrip('/')}"

    logger.info(f"Proxying {request.method} {request.url} -> {target_url} (user_id={x_user_id})")

    try:
        # Подготавливаем headers
        headers = dict(request.headers)
        headers.pop("host", None)
        headers["X-Forwarded-For"] = request.client.host if request.client else ""
        headers["X-Original-Path"] = str(request.url)

        # Получаем тело запроса
        body = await request.body()

        # Отправляем запрос к микросервису
        response = await app.state.http_client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            params=dict(request.query_params)
        )

        # Возвращаем ответ
        return JSONResponse(
            content=response.json() if response.content else {},
            status_code=response.status_code,
            headers=dict(response.headers)
        )

    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=f"Сервис '{service_name}' временно недоступен"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=f"Таймаут при обращении к сервису '{service_name}'"
        )
    except Exception as e:
        logger.error(f"Ошибка при проксировании: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )