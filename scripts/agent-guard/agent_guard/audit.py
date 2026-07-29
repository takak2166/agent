"""Audit log helpers: path validation and secret redaction."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

_BEARER_RE = re.compile(r"(Bearer\s+)(\S+)", re.I)
_SECRET_RE = re.compile(
    r"((?:--?(?:password|token|secret|api[-_]?key))\s*[=:]\s*)(\S+)",
    re.I,
)
_DATA_FLAG_RE = re.compile(
    r"((?:\s|^)(?:-d|--data(?:-binary|-urlencode|-raw)?|--post-data)\s*[=:]?\s*)(\S+)",
    re.I,
)

_MAX_FIELD_LEN = 500


def resolve_audit_path(path: Path, *, base: Path | None = None) -> Path:
    """Resolve audit path and ensure it stays under an allowed base directory."""
    resolved = path.expanduser().resolve()
    candidates: list[Path] = []
    if base is not None:
        candidates.append(base.resolve())
    for env_name in ("AGENT_GUARD_AUDIT_ROOT", "AGENT_GUARD_ROOT"):
        env_val = os.environ.get(env_name)
        if env_val:
            candidates.append(Path(env_val).expanduser().resolve())
    candidates.append(Path.cwd().resolve())

    for candidate in candidates:
        try:
            resolved.relative_to(candidate)
            return resolved
        except ValueError:
            continue
    raise ValueError(f"Audit log path escapes allowed directories: {path}")


def sanitize_action(action: dict[str, Any] | None) -> dict[str, Any] | None:
    """Return a copy of *action* with secrets truncated/redacted."""
    if not action:
        return action
    out = dict(action)
    for key in ("command", "statement"):
        if key in out and isinstance(out[key], str):
            out[key] = _redact_text(out[key])
    return out


def _redact_text(text: str) -> str:
    text = _BEARER_RE.sub(r"\1***", text)
    text = _SECRET_RE.sub(r"\1***", text)
    text = _DATA_FLAG_RE.sub(r"\1***", text)
    if len(text) > _MAX_FIELD_LEN:
        return text[:_MAX_FIELD_LEN] + "…"
    return text


def write_audit(path: Path, record: dict[str, Any]) -> None:
    """Append one JSONL audit record; raises on I/O failure."""
    safe = dict(record)
    if "action" in safe:
        safe["action"] = sanitize_action(safe.get("action"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(safe, ensure_ascii=False) + "\n")
