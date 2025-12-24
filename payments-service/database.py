from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://payments_user:payments_password@localhost:5432/payments_db")

engine = create_engine(DATABASE_URL)

# Создаем таблицы из моделей
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()