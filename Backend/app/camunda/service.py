from __future__ import annotations

import asyncio
import logging
import threading
from collections.abc import Awaitable

from app.camunda import client
from app.core.config import settings

logger = logging.getLogger(__name__)
_background_loop: asyncio.AbstractEventLoop | None = None
_background_thread: threading.Thread | None = None


def _loop_runner(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()


def _ensure_background_loop() -> asyncio.AbstractEventLoop:
    global _background_loop, _background_thread
    if _background_loop and _background_loop.is_running():
        return _background_loop

    loop = asyncio.new_event_loop()
    thread = threading.Thread(
        target=_loop_runner,
        args=(loop,),
        name="camunda-background-loop",
        daemon=True,
    )
    thread.start()
    _background_loop = loop
    _background_thread = thread
    logger.info("Started Camunda background event loop")
    return loop


async def startup() -> None:
    if not settings.camunda_enabled:
        return
    _ensure_background_loop()
    logger.info(
        "Camunda mode enabled. Zeebe address=%s process_id=%s",
        settings.zeebe_address,
        settings.camunda_process_id,
    )
    attempts = 12
    delay_seconds = 5
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            await client.deploy_all_processes()
            logger.info("Camunda BPMN deployment finished")
            return
        except Exception as exc:  # pragma: no cover - integration resilience
            last_error = exc
            logger.warning(
                "Camunda deploy attempt %s/%s failed: %s",
                attempt,
                attempts,
                exc,
                exc_info=True,
            )
            if attempt < attempts:
                await asyncio.sleep(delay_seconds)
    raise RuntimeError("Camunda startup failed after repeated retries") from last_error


async def shutdown() -> None:
    global _background_loop, _background_thread
    if not settings.camunda_enabled:
        return
    if _background_loop and _background_loop.is_running():
        _background_loop.call_soon_threadsafe(_background_loop.stop)
    if _background_thread and _background_thread.is_alive():
        _background_thread.join(timeout=2)
    _background_loop = None
    _background_thread = None
    logger.info("Camunda shutdown complete")


def schedule(coroutine: Awaitable[None]) -> None:
    if not settings.camunda_enabled:
        close = getattr(coroutine, "close", None)
        if callable(close):
            close()
        return

    loop = _ensure_background_loop()
    asyncio.run_coroutine_threadsafe(coroutine, loop)


async def start_timesheet_process(*, timesheet_id: int, user_id: int, actor_id: int | None, month: int, year: int) -> None:
    """
    Camunda integration hook for the timesheet submit action.

    The classic and RabbitMQ variants stay unchanged because this code
    becomes active only when CAMUNDA_ENABLED=true.

    This first version intentionally logs the intended orchestration payload.
    It gives you a clean integration point for a Zeebe client without
    coupling the existing variants to Camunda.
    """
    if not settings.camunda_enabled:
        return

    await client.start_process(
        timesheet_id=timesheet_id,
        user_id=user_id,
        actor_id=actor_id,
        month=month,
        year=year,
    )


async def publish_timesheet_decision(
    *,
    timesheet_id: int,
    actor_id: int | None,
    approved: bool,
    comment: str | None = None,
) -> None:
    if not settings.camunda_enabled:
        return

    await client.publish_decision(
        timesheet_id=timesheet_id,
        actor_id=actor_id,
        approved=approved,
        comment=comment,
    )
