import os
import httpx
from fastapi import FastAPI, Request, Response

app = FastAPI()

# Получаем URL сервисов из переменных окружения, заданных в docker-compose.yml
POSTS_SERVICE_URL = os.getenv("POSTS_SERVICE_URL")
CATEGORIES_SERVICE_URL = os.getenv("CATEGORIES_SERVICE_URL")

# Создаем один клиент для многократного использования, это эффективнее
client = httpx.AsyncClient()


# Универсальный маршрут для проксирования запросов
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_request(request: Request, path: str):
    """
    Эта функция определяет, какому сервису перенаправить запрос,
    основываясь на начальной части URL-пути.
    """

    target_url = None

    # Маршрутизация к сервису постов
    if path.startswith("posts"):
        target_url = f"{POSTS_SERVICE_URL}/{path}"
    # Маршрутизация к сервису категорий
    elif path.startswith("categories"):
        target_url = f"{CATEGORIES_SERVICE_URL}/{path}"

    if not target_url:
        return Response(content="Not Found", status_code=404)

    # Получаем тело запроса
    body = await request.body()

    # Формируем запрос к целевому сервису
    proxied_req = client.build_request(
        method=request.method,
        url=target_url,
        headers=request.headers,
        params=request.query_params,
        content=body
    )

    # Отправляем запрос
    response = await client.send(proxied_req)

    # Возвращаем ответ клиенту
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )
