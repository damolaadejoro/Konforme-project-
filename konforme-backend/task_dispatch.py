"""Run work after the HTTP response without relying on a long-lived process.

On Lambda the execution environment is frozen as soon as a response is returned,
so threads and FastAPI BackgroundTasks cannot be trusted to finish. These helpers
hand the work to the worker Lambda (scans) or run it inline (quick side effects).
Outside Lambda they keep the original thread / BackgroundTasks behaviour.
"""

import json
import os
import threading
from typing import Callable

from fastapi import BackgroundTasks

from config import settings

RUNNING_ON_LAMBDA = bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))


def fire_and_forget(fn: Callable[[], None]) -> None:
    """Run a quick side effect (email, webhook). Inline on Lambda, threaded elsewhere."""
    if RUNNING_ON_LAMBDA:
        fn()
    else:
        threading.Thread(target=fn, daemon=True).start()


def dispatch_worker_task(
    background_tasks: BackgroundTasks,
    payload: dict,
    local_fn: Callable,
    *local_args,
) -> None:
    """Send a task to the worker Lambda, or fall back to BackgroundTasks locally."""
    if settings.worker_function_name:
        import boto3

        boto3.client("lambda").invoke(
            FunctionName=settings.worker_function_name,
            InvocationType="Event",
            Payload=json.dumps(payload).encode(),
        )
    else:
        background_tasks.add_task(local_fn, *local_args)
