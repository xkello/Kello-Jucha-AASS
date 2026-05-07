from __future__ import annotations

import logging

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from app.core.config import settings
from app.messaging.connection import EXCHANGE_NAME, DLX_EXCHANGE_NAME

logger = logging.getLogger(__name__)


class BaseWorker:
    """
    Base class for all RabbitMQ consumers.

    Subclasses must define:
        queue_name   – durable queue name (matches diagram)
        routing_keys – list of topic routing keys to bind

    And implement:
        handle(message) – business logic for each incoming message
    """

    queue_name: str
    routing_keys: list[str]

    async def handle(self, message: AbstractIncomingMessage) -> None:
        raise NotImplementedError

    async def run(self) -> None:
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=10)

            # Declare the dead-letter exchange so it exists before queues reference it
            dlx = await channel.declare_exchange(
                DLX_EXCHANGE_NAME, aio_pika.ExchangeType.FANOUT, durable=True
            )

            # Dead-letter queue for this worker – collects poison messages
            dlq = await channel.declare_queue(
                f"{self.queue_name}.dlq", durable=True
            )
            await dlq.bind(dlx)

            # Main topic exchange
            exchange = await channel.declare_exchange(
                EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
            )

            # Main queue with DLX configured so failed messages land in DLQ
            queue = await channel.declare_queue(
                self.queue_name,
                durable=True,
                arguments={"x-dead-letter-exchange": DLX_EXCHANGE_NAME},
            )
            for key in self.routing_keys:
                await queue.bind(exchange, routing_key=key)

            logger.info(
                "%s started – queue=%s routing_keys=%s",
                self.__class__.__name__,
                self.queue_name,
                self.routing_keys,
            )

            async with queue.iterator() as it:
                async for message in it:
                    async with message.process(requeue=False):
                        # requeue=False means failed messages go to DLQ via DLX
                        try:
                            await self.handle(message)
                        except Exception:
                            logger.exception(
                                "[%s] Unhandled error processing message %s",
                                self.__class__.__name__,
                                message.message_id,
                            )
                            raise  # triggers DLQ routing
