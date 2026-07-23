---
name: kubectl-namespace
description: Ensures the kubectl -n <namespace> flag is placed immediately after the verb. Use when reviewing or writing kubectl commands that include a namespace.
---

# kubectl Command Namespace

Use this skill whenever the user asks about writing or reviewing `kubectl` commands.

- Always structure `kubectl` invocations so that the namespace flag immediately follows the command verb.
- When suggesting or rewriting commands, automatically fix the position of `-n <namespace>`.
- If the user provides a command with `-n` at the end, show the corrected form.

Example:

```bash
# ✅ GOOD
kubectl get -n <namespace> pods
kubectl describe -n <namespace> deployment/my-app

# ❌ BAD
kubectl get pods -n <namespace>
kubectl describe deployment/my-app -n <namespace>
```
