import json
import os
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from threading import Lock

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, CONTENT_TYPE_LATEST, generate_latest

EMAIL = os.environ.get("EMAIL", "23f2001912@ds.study.iitm.ac.in")
START_TIME = time.monotonic()
LOG_LIMIT = 1000
_logs = deque(maxlen=LOG_LIMIT)
_logs_lock = Lock()

# Use a private registry to avoid duplicate registration during server reloads.
from prometheus_client import CollectorRegistry
registry = CollectorRegistry()
REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests received by this service",
    ["method", "path", "status"],
    registry=registry,
)

app = FastAPI(title="Prometheus Observability Service")


def add_log(entry):
    with _logs_lock:
        _logs.append(entry)


@app.middleware("http")
async def observe_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    path = request.url.path
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        REQUESTS.labels(request.method, path, str(status)).inc()
        add_log({
            "level": "INFO" if status < 500 else "ERROR",
            "ts": datetime.now(timezone.utc).isoformat(),
            "path": path,
            "request_id": request_id,
            "method": request.method,
            "status": status,
        })


@app.get("/work")
def work(n: int = 1):
    if n < 0:
        n = 0
    # Do a small deterministic amount of work without unnecessary delay.
    done = sum(1 for _ in range(n))
    return {"email": EMAIL, "done": done}


@app.get("/healthz")
def healthz():
    return {"status": "ok", "uptime_s": max(0.0, time.monotonic() - START_TIME)}


@app.get("/logs/tail")
def logs_tail(limit: int = 20):
    limit = max(0, min(limit, LOG_LIMIT))
    with _logs_lock:
        entries = list(_logs)[-limit:] if limit else []
    return entries


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return PlainTextResponse(
        generate_latest(registry).decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST,
    )
