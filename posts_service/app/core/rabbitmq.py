import asyncio
import uuid
from typing import Optional

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL")

class RpcClient:
    """Асинхронный RPC клиент для RabbitMQ."""

    def __init__(self, amqp_url: str = RABBITMQ_URL):
        self.amqp_url = amqp_url # URL для подключения к RabbitMQ
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.callback_queue: Optional[aio_pika.Queue] = None
        self.futures = {} # {correlation_id: Future}; Future будет завершено, когда придет ответ на соотве-ий вопрос
        self.loop = asyncio.get_running_loop() # создаем цикл событий asyncioир

    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.amqp_url, loop=self.loop) # создаем robust (крепкое соединение)
        self.channel = await self.connection.channel() # Создается канал внутри соединения.
        # Все операции с очередями и сообщениями выполняются через канал
        self.callback_queue = await self.channel.declare_queue(exclusive=True) # Создается уникальная очередь обратного вызова
        # Эксклюзивные очереди доступны только для объявляющего соединения и удаляются, когда это соединение закрывается
        await self.callback_queue.consume(self.on_response, no_ack=True) # Начинается потребление из callback_queue.
        # Каждое сообщение будет передаваться в метод on_response, no_ack - подтверждать получение смс не требуется

    async def close(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    def on_response(self, message: AbstractIncomingMessage):
        future = self.futures.pop(message.correlation_id, None)
        if future:
            future.set_result(message.body)

    async def call(self, body: str, routing_key: str) -> Optional[bytes]:
        # Проверяем, что connection доступен
        if not self.connection or self.connection.is_closed:
            raise ConnectionError('RPC client is not connected')

        correlation_id = str(uuid.uuid4())
        future = self.loop.create_future()
        self.futures[correlation_id] = future

        await self.channel.default_exchange.publish( # Публикация сообщения в RabbitMQ
            aio_pika.Message(
                body=body.encode(),
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name # Куда отправлять полученное сообщение
            ),
            routing_key=routing_key # В какую очередь отправлять для получения ответа
        )

        try:
            return await asyncio.wait_for(future, timeout=5.0)
        except asyncio.TimeoutError:
            self.futures.pop(correlation_id, None)
            return None

class RabbitMQCategoryValidator:
    """Конкретная реализация валидатора категорий через RabbitMQ RPC."""

    def __init__(self):
        self.rpc_client = RpcClient()

    async def connect(self):
        await self.rpc_client.connect()

    async def close(self):
        await self.rpc_client.close()

    async def check_exists(self, category_id: int) -> bool:
        response = await self.rpc_client.call(str(category_id), 'category_check_queue')
        if response is None:
            return False
        return response == b'true'

category_validator_instance = RabbitMQCategoryValidator()


