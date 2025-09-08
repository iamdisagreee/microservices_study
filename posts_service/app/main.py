from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import posts
from app.core.database import create_db_and_tables
from app.core.rabbitmq import category_validator_instance


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Приложение запускается. Создаем базу данных...")
    await create_db_and_tables()
    print("База данных инициализирована.")
    await category_validator_instance.connect()  # Подключаемся к RabbitMQ
    yield
    await category_validator_instance.close()
    print("Приложение завершает работу.")


app = FastAPI(
    title="Сервис для постов",
    lifespan=lifespan
)

app.include_router(posts.router)


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {"message": "Это проект из курса 'Продвинутый FastAPI для продолжающих'"}
