import json
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from time import monotonic
from typing import Literal

from fastapi import FastAPI, Header, HTTPException
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from pydantic import BaseModel, Field

app = FastAPI(title="AIOps Investigator")
TARGET_NAMESPACE = os.getenv("TARGET_NAMESPACE", "mavencrest")
REPORT_DIR = Path(os.getenv("REPORT_DIR", "/reports"))
WEBHOOK_TOKEN = os.environ["WEBHOOK_TOKEN"]
if not WEBHOOK_TOKEN:
    raise RuntimeError("WEBHOOK_TOKEN must not be empty")

lock = Lock()
completed = {}


class Alert(BaseModel):
    status: Literal["firing", "resolved"]
    labels: dict[str, str]


class Webhook(BaseModel):
    alerts: list[Alert] = Field(max_length=5)


def redact(text):
    text = re.sub(
        r"(?i)(password|token|secret|api[_-]?key|authorization)"
        r"(\s*[:=]\s*)([^\s,;]+)",
        r"\1\2[REDACTED]",
        text,
    )
    return re.sub(
        r"(://)[^/\s:@]+:[^/\s@]+@",
        r"\1[REDACTED]@",
        text,
    )


def collect(api, namespace, pod_name):
    pod = api.read_namespaced_pod(
        pod_name, namespace, _request_timeout=10
    )
    evidence = {
        "namespace": namespace,
        "pod": pod_name,
        "uid": pod.metadata.uid,
        "phase": pod.status.phase,
        "containers": [],
        "events": [],
    }

    for status in (pod.status.container_statuses or [])[:3]:
        item = {
            "name": status.name,
            "ready": status.ready,
            "restarts": status.restart_count,
            "state": api.api_client.sanitize_for_serialization(status.state),
            "previous_state": api.api_client.sanitize_for_serialization(
                status.last_state
            ),
        }
        for previous in (False, True):
            if previous and status.restart_count == 0:
                continue
            key = "previous_logs" if previous else "current_logs"
            try:
                item[key] = api.read_namespaced_pod_log(
                    pod_name,
                    namespace,
                    container=status.name,
                    previous=previous,
                    tail_lines=80,
                    limit_bytes=6000,
                    timestamps=True,
                    _request_timeout=10,
                )
            except ApiException as exc:
                item[key] = f"Unavailable: HTTP {exc.status}"
        evidence["containers"].append(item)

    try:
        events = api.list_namespaced_event(
            namespace,
            field_selector=f"involvedObject.uid={pod.metadata.uid}",
            _request_timeout=10,
        )
        evidence["events"] = [
            {"reason": e.reason, "message": e.message, "count": e.count}
            for e in events.items[-20:]
        ]
    except ApiException as exc:
        evidence["events_error"] = f"Unavailable: HTTP {exc.status}"

    # Redaction is best effort; this version does not send data externally.
    return json.loads(redact(json.dumps(evidence, default=str)))


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.post("/webhook")
def investigate(payload: Webhook, authorization: str = Header(default="")):
    if not secrets.compare_digest(
        authorization, f"Bearer {WEBHOOK_TOKEN}"
    ):
        raise HTTPException(401, "Invalid webhook credential")

    if not lock.acquire(blocking=False):
        raise HTTPException(503, "Investigation already running; retry later")

    try:
        config.load_incluster_config()
        api = client.CoreV1Api()
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        now = monotonic()
        for key in list(completed):
            if now - completed[key] >= 900:
                del completed[key]

        reports = []
        for alert in payload.alerts:
            namespace = alert.labels.get("namespace")
            pod_name = alert.labels.get("pod")
            alert_name = alert.labels.get("alertname", "unknown")

            if (
                alert.status != "firing"
                or namespace != TARGET_NAMESPACE
                or not pod_name
            ):
                continue

            key = (namespace, pod_name, alert_name)
            if key in completed:
                continue

            try:
                evidence = collect(api, namespace, pod_name)
            except ApiException as exc:
                raise HTTPException(
                    503, f"Kubernetes evidence unavailable: HTTP {exc.status}"
                ) from exc

            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            filename = f"{stamp}-{secrets.token_hex(4)}.json"
            report = {
                "stage": "evidence-only",
                "alert": alert_name,
                "collected_at": stamp,
                "evidence": evidence,
            }
            temporary = REPORT_DIR / f".{filename}.tmp"
            temporary.write_text(json.dumps(report, indent=2))
            temporary.replace(REPORT_DIR / filename)
            completed[key] = monotonic()
            reports.append(filename)

        return {"reports": reports}
    finally:
        lock.release()
