from __future__ import annotations

import logging

import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel, AbstractRobustExchange

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "aass.events"
DLX_EXCHANGE_NAME = "aass.events.dlx"

_connection: AbstractRobustConnection | None = None
_channel: AbstractRobustChannel | None = None
_exchange: AbstractRobustExchange | None = None


async def connect(url: str) -> None:
    """Open a robust (auto-reconnecting) connection and declare the topic exchange."""
    global _connection, _channel, _exchange
    _connection = await aio_pika.connect_robust(url)
    _channel = await _connection.channel()
    await _channel.set_qos(prefetch_count=10)

    # Dead-letter exchange – receives messages that exceed retry limits
    await _channel.declare_exchange(DLX_EXCHANGE_NAME, aio_pika.ExchangeType.FANOUT, durable=True)

    _exchange = await _channel.declare_exchange(
        EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
    )
    logger.info("RabbitMQ connected. Exchange: %s", EXCHANGE_NAME)


async def disconnect() -> None:
    """Close the connection cleanly on app shutdown."""
    global _connection, _channel, _exchange
    if _connection and not _connection.is_closed:
        await _connection.close()
    _connection = None
    _channel = None
    _exchange = None
    logger.info("RabbitMQ disconnected")


def get_exchange() -> AbstractRobustExchange | None:
    return _exchange
