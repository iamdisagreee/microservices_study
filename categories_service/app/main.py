import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import categories
from app.core.database import create_db_and_tables

from app.core.rabbitmq_worker import run_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Приложение запускается. Создаем базу данных...")
    consumer_task = asyncio.create_task(run_consumer())
    print('Запустили consumer')
    await create_db_and_tables()
    print("База данныха инициализирована.")
    yield
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        print("Consumer RabbitMQ успешно остановлен.")

    print("Приложение завершает работу.")


app = FastAPI(
    title="Сервис для категорий",
    lifespan=lifespan
)

app.include_router(categories.router)


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {"message": "Это проект из курса 'Продвинутый FastAPI для продолжающих'"}
