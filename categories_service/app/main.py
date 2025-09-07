from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import categories
from app.core.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Приложение запускается. Создаем базу данных...")
    await create_db_and_tables()
    print("База данных инициализирована.")
    yield
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
