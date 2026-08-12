import logging
import sys
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("epiderm.flow")

# Single shared file so API + consumer + diagnosis worker steps appear in one place.
_FLOW_LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "epiderm-flow.log"


def _ensure_logger() -> None:
    if logger.handlers:
        return

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s %(message)s")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    _FLOW_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(_FLOW_LOG_PATH, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def flow_log(
    step: str,
    component: str,
    message: str,
    *,
    consult_id: Optional[str] = None,
    **fields: Any,
) -> None:
    """Emit a sequenced flow log so request progress is easy to grep across processes."""
    _ensure_logger()
    parts = [f"[FLOW] step={step} component={component}"]
    if consult_id is not None:
        parts.append(f"consult_id={consult_id}")
    for key, value in fields.items():
        if value is not None:
            parts.append(f"{key}={value}")
    parts.append(f"| {message}")
    logger.info(" ".join(parts))
