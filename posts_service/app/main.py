import logging
from contextlib import asynccontextmanager
from typing import Dict
import time
from fastapi import FastAPI, Depends, Request
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter
from redis import asyncio as aioredis
from pydantic import BaseModel
from app.routers import posts
from app.core.database import create_db_and_tables
from app.core.rabbitmq import category_validator_instance
from app.core.logging_config import logger


# from app.core.redis_connect import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = aioredis.from_url("redis://redis:6379/0")
    redis_client_2 = aioredis.from_url("redis://redis:6379/1")
    logger.info("Loading server...")
    try:
        await create_db_and_tables()
        await category_validator_instance.connect()  # Подключаемся к RabbitMQ

        await redis_client.ping()
        FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
        await FastAPILimiter.init(redis_client_2)
        # print("Успешное подключение ка Redis!")
        yield
    except aioredis.ConnectionError as e:
        # redis_client = None
        # print(f"Не удалось подключиться к Redis: {e}")
        # В продакшене можно реализовать запасной вариант, например, in-memory кэш
        raise
    except Exception as e:
        raise
    finally:
        await category_validator_instance.close()
        # if redis_client:
        await redis_client.close()
        # print("Приложение завершает работу.")


app = FastAPI(
    title="Сервис для постов",
    lifespan=lifespan
)

app.include_router(posts.router)

# import logging
#
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
#
# # Обработчик для файла
# file_handler = logging.FileHandler('app.log')
# file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
#
# # Обработчик для консоли
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
#
# # Добавление обработчиков
# logger.addHandler(file_handler)
# logger.addHandler(console_handler)
#
# logger.info("Это сообщение будет в консоли и в файле")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Выполняем запрос
    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)

    logger.info({
        "request_path": str(request.url.path),
        # URL может быть сложным объектом, лучше преобразовать в строку
        "method": request.method,
        "status_code": response.status_code,
        "process_time_ms": f"{process_time:.2f}",
        "client_ip": request.client.host
    })
    return response


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {"message": "Это проект из курса 'Продвинутый FastAPI для продолжающих'"}

