from fastapi import FastAPI, Depends, HTTPException, Header, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
from datetime import datetime
import asyncio
import logging
from contextlib import asynccontextmanager

from database import get_db
from models import Order, OrderStatus, OutboxMessage
from schemas import OrderCreate, OrderResponse
from websocket_manager import ws_manager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Управление жизненным циклом приложения ---
@asynccontextmanager
async def lifespan(app: FastAPI):

    # 1. Подключаемся к Redis (для обмена сообщениями между инстансами)
    await ws_manager.connect_redis()

    # 2. Запускаем фоновую задачу прослушивания канала обновлений
    asyncio.create_task(ws_manager.listen_to_redis())

    logger.info("Сервис заказов запущен, Redis подключен.")

    yield  # Здесь приложение работает

    # 3. При остановке отключаемся
    await ws_manager.disconnect_redis()
    logger.info("Сервис заказов остановлен.")


app = FastAPI(title="Orders Service", version="2.0.0", lifespan=lifespan)


# --- Зависимости (Dependencies) ---

async def verify_user_id(x_user_id: int = Header(..., alias="X-User-ID")):
    """
    Проверяет наличие обязательного заголовка X-User-ID.
    Эмулирует аутентификацию пользователя.
    """
    if x_user_id <= 0:
        raise HTTPException(status_code=400, detail="Неверный ID пользователя")
    return x_user_id


# --- WebSocket Эндпоинт ---

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await ws_manager.connect(websocket, user_id)
    try:
        # Отправляем приветственное сообщение при подключении
        await websocket.send_json({
            "type": "connection_established",
            "message": f"Подключено к Сервису Заказов (Инстанс {ws_manager.instance_id})"
        })

        # Слушаем сообщения от клиента, чтобы соединение не разрывалось
        while True:
            try:
                data = await websocket.receive_json()
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except:
                break
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)


# --- REST API Эндпоинты ---

@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    # Проверяем, жива ли база данных
    db.execute(text("SELECT 1"))
    return {"status": "healthy", "instance_id": ws_manager.instance_id}


@app.post("/orders", response_model=OrderResponse, status_code=201, tags=["Orders"])
async def create_order(
        data: OrderCreate,
        user_id: int = Depends(verify_user_id),
        db: Session = Depends(get_db)
):

    try:
        # Начинаем транзакцию базы данных
        db.begin()

        # 1. Сохраняем сам заказ в таблицу orders
        order = Order(
            user_id=user_id,
            amount=data.amount,
            description=data.description,
            status=OrderStatus.NEW
        )
        db.add(order)
        db.flush()  # Получаем ID заказа, не завершая транзакцию

        # 2. Сохраняем сообщение в таблицу outbox_messages
        outbox = OutboxMessage(
            event_type="order_created",
            event_data=json.dumps({
                "order_id": order.id,
                "user_id": user_id,
                "amount": order.amount,
                "timestamp": datetime.now().isoformat()
            })
        )
        db.add(outbox)

        # Фиксируем транзакцию
        db.commit()

        # 3. Мгновенно отправляем уведомление на фронтенд через WebSocket
        await ws_manager.broadcast_order_update(
            order_id=order.id,
            user_id=user_id,
            status=order.status.value,
            amount=order.amount
        )

        # Возвращаем созданный объект
        return OrderResponse.model_validate(order)

    except Exception as e:
        # В случае любой ошибки откатываем транзакцию
        db.rollback()
        logger.error(f"Ошибка при создании заказа: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")


@app.get("/orders", response_model=list[OrderResponse], tags=["Orders"])
async def get_orders(user_id: int = Depends(verify_user_id), db: Session = Depends(get_db)):
    """
    Получить список всех заказов текущего пользователя.
    """
    orders = db.query(Order).filter(
        Order.user_id == user_id
    ).order_by(Order.created_at.desc()).all()

    return [OrderResponse.model_validate(o) for o in orders]


@app.get("/orders/{order_id}", response_model=OrderResponse, tags=["Orders"])
async def get_order(
        order_id: int,
        user_id: int = Depends(verify_user_id),
        db: Session = Depends(get_db)
):
    """
    Получить детали конкретного заказа по ID.
    """
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user_id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    return OrderResponse.model_validate(order)