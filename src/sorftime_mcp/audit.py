import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SENSITIVE_KEY_PARTS = ("authorization", "token", "secret", "password", "api_key", "sk")
LONG_VALUE_KEYS = ("image",)


class AuditLogger:
    def __init__(self, path: Path | None = None, *, emit_stdout: bool = True) -> None:
        self._path = path
        self._emit_stdout = emit_stdout
        if self._path is not None:
            self._path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, record: dict[str, Any]) -> None:
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        if self._emit_stdout:
            sys.stdout.write(f"{line}\n")
            sys.stdout.flush()
        if self._path is not None:
            with self._path.open("a", encoding="utf-8") as file:
                file.write(f"{line}\n")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sanitize_for_audit(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            lower_key = str(key).lower()
            if any(part in lower_key for part in SENSITIVE_KEY_PARTS):
                sanitized[key] = "[REDACTED]"
            elif any(part in lower_key for part in LONG_VALUE_KEYS):
                sanitized[key] = summarize_long_value(item)
            else:
                sanitized[key] = sanitize_for_audit(item)
        return sanitized
    if isinstance(value, list):
        return [sanitize_for_audit(item) for item in value]
    if isinstance(value, str):
        return summarize_long_value(value)
    return value


def summarize_long_value(value: Any) -> Any:
    if not isinstance(value, str):
        return sanitize_for_audit(value)
    if len(value) <= 180:
        return value
    return f"{value[:80]}...[truncated:{len(value)}]"
