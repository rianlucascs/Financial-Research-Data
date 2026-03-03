from datetime import datetime, timezone
import socket


def build_checkpoint_payload(
    *,
    pipeline: str,
    stage: str,
    step: str,
    status: str,
    run_id: str | None,
    environment: str | None,
    failure_point: str | None = None,
    source: str = "B3",
    extra: dict | None = None,
) -> dict:
    """Monta payload base padronizado para checkpoints."""
    payload = {
        "pipeline": pipeline,
        "stage": stage,
        "step": step,
        "status": status,
        "failure_point": failure_point,
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "host": socket.gethostname(),
        "environment": environment,
    }
    if extra:
        payload.update(extra)
    return payload
