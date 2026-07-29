"""Shared policy vocabulary for SQL, HTTP, and kubectl classification."""

from __future__ import annotations

SQL_MUTATE_OPS = frozenset(
    {
        "insert",
        "update",
        "delete",
        "drop",
        "truncate",
        "alter",
        "create",
        "grant",
        "revoke",
        "replace",
        "merge",
        "copy",
        "call",
    }
)

SQL_READ_OPS = frozenset(
    {
        "select",
        "show",
        "describe",
        "explain",
        "with",
    }
)

HTTP_READ_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
HTTP_MUTATE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

KUBECTL_READ_VERBS = frozenset(
    {
        "get",
        "describe",
        "logs",
        "top",
        "api-resources",
        "api-versions",
        "explain",
        "cluster-info",
        "config",
        "version",
        "auth",
        "wait",
    }
)

KUBECTL_MUTATE_VERBS = frozenset(
    {
        "apply",
        "create",
        "delete",
        "edit",
        "patch",
        "replace",
        "scale",
        "rollout",
        "exec",
        "attach",
        "cp",
        "drain",
        "cordon",
        "uncordon",
        "taint",
        "label",
        "annotate",
        "set",
    }
)

# kubectl global flags that take a separate argument value
KUBECTL_VALUE_FLAGS = frozenset(
    {
        "-n",
        "--namespace",
        "--context",
        "-c",
        "--cluster",
        "--user",
        "--kubeconfig",
    }
)
