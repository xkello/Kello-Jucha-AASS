from __future__ import annotations

import logging
from pathlib import Path

from pyzeebe import ZeebeClient, create_insecure_channel

from app.core.config import settings

logger = logging.getLogger(__name__)

_channel = None
_client: ZeebeClient | None = None


def get_processes_path() -> Path:
    return Path(__file__).resolve().parents[2] / "camunda" / "processes"


def get_client() -> ZeebeClient:
    global _channel, _client
    if _client is None:
        _channel = create_insecure_channel(grpc_address=settings.zeebe_address)
        _client = ZeebeClient(_channel)
    return _client


async def deploy_all_processes() -> None:
    client = get_client()
    processes_path = get_processes_path()
    for process_file in sorted(processes_path.glob("*.bpmn")):
        await client.deploy_resource(str(process_file))
        logger.info("[Camunda] Deployed BPMN: %s", process_file.name)


async def start_process(*, timesheet_id: int, user_id: int, actor_id: int | None, month: int, year: int) -> None:
    client = get_client()
    variables = {
        "timesheetId": timesheet_id,
        "userId": user_id,
        "actorId": actor_id,
        "month": month,
        "year": year,
        "isValid": False,
        "approved": False,
        "managerId": None,
        "validationComment": None,
        "comment": None,
    }
    process_instance_key = await client.run_process(
        bpmn_process_id=settings.camunda_process_id,
        variables=variables,
    )
    logger.info(
        "[Camunda] Process instance started: process_id=%s instance_key=%s timesheet_id=%s",
        settings.camunda_process_id,
        process_instance_key,
        timesheet_id,
    )


async def publish_decision(*, timesheet_id: int, actor_id: int | None, approved: bool, comment: str | None = None) -> None:
    client = get_client()
    variables = {
        "timesheetId": timesheet_id,
        "actorId": actor_id,
        "approved": approved,
        "comment": comment,
    }
    await client.publish_message(
        name="timesheet.decision",
        correlation_key=str(timesheet_id),
        variables=variables,
    )
    logger.info(
        "[Camunda] Published manager decision: timesheet_id=%s approved=%s",
        timesheet_id,
        approved,
    )
