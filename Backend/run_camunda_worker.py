from __future__ import annotations

import asyncio
import logging

from app.camunda.worker import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logging.getLogger("pyzeebe.worker.job_poller").setLevel(logging.ERROR)


if __name__ == "__main__":
    asyncio.run(run())
