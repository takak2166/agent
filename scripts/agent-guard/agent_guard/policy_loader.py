"""Load rules.yaml: shared vocab, generated patterns, and resolved rules."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

try:
    import yaml
except ImportError as e:  # pragma: no cover
    raise ImportError("PyYAML is required: python3 -m pip install pyyaml") from e

_VOCAB_REF = re.compile(r"^\$vocab\.([a-z_]+)$")
_PATTERN_REF = re.compile(r"^\$pattern\.([a-z_]+)$")

_REQUIRED_VOCAB_KEYS = (
    "sql_mutate",
    "sql_read",
    "http_mutate",
    "http_read",
    "kubectl_mutate",
    "kubectl_read",
    "kubectl_value_flags",
    "sql_clients",
    "http_clients",
    "gh_read",
    "gh_write",
)


@dataclass(frozen=True)
class Vocab:
    sql_mutate: frozenset[str]
    sql_read: frozenset[str]
    http_mutate: frozenset[str]
    http_read: frozenset[str]
    kubectl_mutate: frozenset[str]
    kubectl_read: frozenset[str]
    kubectl_value_flags: frozenset[str]
    sql_clients: frozenset[str]
    http_clients: frozenset[str]
    gh_read: frozenset[str]
    gh_write: frozenset[str]

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> "Vocab":
        missing = [k for k in _REQUIRED_VOCAB_KEYS if k not in raw]
        if missing:
            raise ValueError(f"vocab missing keys: {', '.join(missing)}")
        return cls(
            sql_mutate=_as_lower_set(raw["sql_mutate"]),
            sql_read=_as_lower_set(raw["sql_read"]),
            http_mutate=_as_upper_set(raw["http_mutate"]),
            http_read=_as_upper_set(raw["http_read"]),
            kubectl_mutate=_as_lower_set(raw["kubectl_mutate"]),
            kubectl_read=_as_lower_set(raw["kubectl_read"]),
            kubectl_value_flags=frozenset(str(x) for x in raw["kubectl_value_flags"]),
            sql_clients=_as_lower_set(raw["sql_clients"]),
            http_clients=_as_lower_set(raw["http_clients"]),
            gh_read=_as_lower_set(raw["gh_read"]),
            gh_write=_as_lower_set(raw["gh_write"]),
        )


@dataclass(frozen=True)
class CompiledVocab:
    """Vocab plus regexes derived from it (built once per policy load)."""

    vocab: Vocab
    sql_mutate_re: re.Pattern[str]
    sql_read_re: re.Pattern[str]
    http_method_re: re.Pattern[str]
    http_method_eq_re: re.Pattern[str]
    httpie_mutate_re: re.Pattern[str]
    mutating_http_flags_re: re.Pattern[str]
    sql_client_re: re.Pattern[str]
    http_client_re: re.Pattern[str]


@dataclass(frozen=True)
class PolicyDocument:
    default: str
    rules: list[dict[str, Any]]
    vocab: Vocab
    compiled: CompiledVocab
    patterns: dict[str, str]


class PolicyLoader:
    _cache: ClassVar[dict[tuple[str, int], PolicyDocument]] = {}

    @classmethod
    def load(cls, path: str | Path) -> PolicyDocument:
        path = Path(path)
        mtime = path.stat().st_mtime_ns
        key = (str(path.resolve()), mtime)
        cached = cls._cache.get(key)
        if cached is not None:
            return cached
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        doc = cls._parse(data)
        cls._cache[key] = doc
        return doc

    @classmethod
    def clear_cache(cls) -> None:
        cls._cache.clear()

    @classmethod
    def _parse(cls, data: dict[str, Any]) -> PolicyDocument:
        if not isinstance(data, dict):
            raise ValueError("policy document must be a mapping")
        raw_vocab = data.get("vocab")
        if not isinstance(raw_vocab, dict):
            raise ValueError("vocab section is required")
        vocab = Vocab.from_mapping(raw_vocab)
        patterns = _build_patterns(vocab)
        raw_rules = data.get("rules")
        if not isinstance(raw_rules, list):
            raise ValueError("rules must be a list")
        resolved_rules = [_resolve_rule(rule, vocab, patterns) for rule in raw_rules]
        default = str(data.get("default", "deny")).lower()
        if default not in ("allow", "deny"):
            raise ValueError("default must be allow or deny")
        return PolicyDocument(
            default=default,
            rules=resolved_rules,
            vocab=vocab,
            compiled=_compile_vocab(vocab),
            patterns=patterns,
        )


def default_rules_path() -> Path:
    return Path(__file__).resolve().parent.parent / "rules.yaml"


def get_policy(path: str | Path | None = None) -> PolicyDocument:
    return PolicyLoader.load(path or default_rules_path())


def get_vocab(path: str | Path | None = None) -> Vocab:
    return get_policy(path).vocab


def get_compiled_vocab(path: str | Path | None = None) -> CompiledVocab:
    return get_policy(path).compiled


def _as_lower_set(value: Any) -> frozenset[str]:
    if not isinstance(value, list) or not value:
        raise ValueError("vocab list must be a non-empty list")
    return frozenset(str(x).lower() for x in value)


def _as_upper_set(value: Any) -> frozenset[str]:
    if not isinstance(value, list) or not value:
        raise ValueError("vocab list must be a non-empty list")
    return frozenset(str(x).upper() for x in value)


def _alt_join(words: frozenset[str], *, upper: bool = False) -> str:
    items = sorted(words, key=len, reverse=True)
    if upper:
        items = [w.upper() for w in items]
    return "|".join(re.escape(w) for w in items)


_HTTP_MUTATE_BODY_FLAGS = (
    r"\s-d\s|--data(?:-binary|-urlencode|-raw)?(?:=|\s|--)|"
    r"--json\s|-T\s|--upload-file\s|-F\s|--form\s|"
    r"--post-data(?:=|\s)|--post-file(?:=|\s)|--body-file(?:=|\s)"
)


def _build_patterns(vocab: Vocab) -> dict[str, str]:
    kubectl_mutate = _alt_join(vocab.kubectl_mutate)
    sql_mutate = _alt_join(vocab.sql_mutate, upper=True)
    sql_clients = _alt_join(vocab.sql_clients)
    http_clients = _alt_join(vocab.http_clients)
    http_mutate = _alt_join(vocab.http_mutate, upper=True)
    return {
        "sql_mutate_shell": (
            rf"(?i)(^|[;&|\n]\s*)({sql_clients})\b.*\b({sql_mutate})\b"
        ),
        "http_mutate_shell": (
            rf"(?i)(^|[;&|\n]\s*)({http_clients})\b.*("
            rf"(-X|--request|--method)\s*({http_mutate})\b|--method=({http_mutate})\b|"
            rf"{_HTTP_MUTATE_BODY_FLAGS}|"
            rf"--method\s+({http_mutate})\b|"
            rf"\bhttps?\s+({http_mutate})\b)"
        ),
    }


def _compile_vocab(vocab: Vocab) -> CompiledVocab:
    sql_mutate = _alt_join(vocab.sql_mutate, upper=True)
    sql_read = _alt_join(vocab.sql_read, upper=True)
    all_http = _alt_join(vocab.http_read | vocab.http_mutate, upper=True)
    http_mutate = _alt_join(vocab.http_mutate, upper=True)
    sql_clients = _alt_join(vocab.sql_clients)
    http_clients = _alt_join(vocab.http_clients)
    return CompiledVocab(
        vocab=vocab,
        sql_mutate_re=re.compile(rf"\b({sql_mutate})\b", re.I),
        sql_read_re=re.compile(rf"\b({sql_read})\b", re.I),
        http_method_re=re.compile(
            rf"(?:(?:-X|--request|--method)\s*)({all_http})\b",
            re.I,
        ),
        http_method_eq_re=re.compile(rf"--method=({all_http})\b", re.I),
        httpie_mutate_re=re.compile(
            rf"(^|[;&|]\s*)(?:http|https)\s+({http_mutate})\b",
            re.I,
        ),
        mutating_http_flags_re=re.compile(
            rf"({_HTTP_MUTATE_BODY_FLAGS}|--method\s+({http_mutate})\b)",
            re.I,
        ),
        sql_client_re=re.compile(rf"(^|[;&|]\s*)({sql_clients})\b", re.I),
        http_client_re=re.compile(rf"(^|[;&|]\s*)({http_clients})\b", re.I),
    )


def _resolve_rule(rule: Any, vocab: Vocab, patterns: dict[str, str]) -> dict[str, Any]:
    if not isinstance(rule, dict):
        raise ValueError(f"each rule must be a mapping, got {type(rule).__name__}")
    rule_id = rule.get("id")
    if not rule_id:
        raise ValueError("rule missing id")
    raw_match = rule.get("match") or {}
    if not isinstance(raw_match, dict):
        raise ValueError(f"rule {rule_id!r}: match must be a mapping")
    resolved_match = {key: _resolve_value(value, vocab, patterns) for key, value in raw_match.items()}
    return {**rule, "match": resolved_match}


def _resolve_value(value: Any, vocab: Vocab, patterns: dict[str, str]) -> Any:
    if isinstance(value, str):
        vocab_match = _VOCAB_REF.match(value)
        if vocab_match:
            key = vocab_match.group(1)
            try:
                return sorted(getattr(vocab, key))
            except AttributeError as exc:
                raise ValueError(f"unknown vocab key: {key}") from exc
        pattern_match = _PATTERN_REF.match(value)
        if pattern_match:
            key = pattern_match.group(1)
            if key not in patterns:
                raise ValueError(f"unknown pattern key: {key}")
            return patterns[key]
    return value
