from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextvars import ContextVar
from typing import Optional
import os
from models import Base
from sqlalchemy.exc import OperationalError, ProgrammingError, IntegrityError
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем URL базы данных из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://orders_user:orders_password@localhost:5432/orders_db")

# Создаем движок SQLAlchemy
engine = create_engine(DATABASE_URL)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Инициализация БД с защитой от Race Condition ---
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Таблицы базы данных успешно проверены/созданы.")
except (OperationalError, ProgrammingError, IntegrityError) as e:
    logger.warning(f"Инициализация БД пропущена (вероятно, таблицы уже созданы другим инстансом): {e}")

# Переменная контекста для асинхронной работы с сессией в разных потоках
db_session: ContextVar[Optional[Session]] = ContextVar('db_session', default=None)

# Функция-генератор для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()