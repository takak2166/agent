#!/usr/bin/env bash
# Check RKE2/Kubernetes version against endoflife.date and optionally notify Slack.
set -euo pipefail

WARN_DAYS_BEFORE_EOL="${WARN_DAYS_BEFORE_EOL:-90}"
CLUSTER_NAME="${CLUSTER_NAME:-unknown}"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

resolve_k8s_version() {
  if [[ -n "${K8S_VERSION:-}" ]]; then
    echo "$K8S_VERSION"
    return
  fi
  if command -v kubectl >/dev/null 2>&1; then
    kubectl version -o json 2>/dev/null | jq -r '.serverVersion.gitVersion // empty'
    return
  fi
  echo "ERROR: set K8S_VERSION or configure kubectl" >&2
  exit 1
}

parse_minor() {
  # v1.32.13+rke2r2 -> 1.32
  echo "$1" | sed -E 's/^v?([0-9]+\.[0-9]+).*/\1/'
}

days_until() {
  local target="$1"
  local now epoch_target epoch_now
  epoch_now=$(date -u +%s)
  epoch_target=$(date -u -d "$target" +%s 2>/dev/null || date -u -j -f "%Y-%m-%d" "$target" +%s)
  echo $(( (epoch_target - epoch_now) / 86400 ))
}

raw_version=$(resolve_k8s_version)
minor=$(parse_minor "$raw_version")

eol_json=$(curl -fsSL "https://endoflife.date/api/kubernetes.json")
eol_date=$(echo "$eol_json" | jq -r --arg m "$minor" '.[] | select(.cycle == $m) | .eol // empty')
latest_patch=$(echo "$eol_json" | jq -r --arg m "$minor" '.[] | select(.cycle == $m) | .latest // empty')

if [[ -z "$eol_date" ]]; then
  echo "WARN: no EOL entry for Kubernetes $minor (version: $raw_version)" >&2
  exit 0
fi

days_left=$(days_until "$eol_date")
rke2_stable=$(curl -fsSL "https://update.rke2.io/v1-release/channels" | jq -r '.data[] | select(.name == "stable") | .latest')

status="ok"
if (( days_left < 0 )); then
  status="past_eol"
elif (( days_left <= WARN_DAYS_BEFORE_EOL )); then
  status="warning"
fi

if [[ "$status" == "past_eol" ]]; then
  icon="🚨"
  title="RKE2/k8s バージョン警告（EOL 超過）"
elif [[ "$status" == "warning" ]]; then
  icon="⚠️"
  title="RKE2/k8s バージョン警告"
else
  icon="✅"
  title="RKE2/k8s バージョン確認"
fi

if (( days_left < 0 )); then
  eol_label="EOL から $(( -days_left )) 日経過"
else
  eol_label="あと ${days_left} 日"
fi

message="${icon} ${title}

クラスタ: ${CLUSTER_NAME}
現在: ${raw_version} (Kubernetes ${minor})
最新パッチ (上流): ${latest_patch}
EOL: ${eol_date}（${eol_label}）
RKE2 stable: ${rke2_stable}"

if [[ "$status" != "ok" ]]; then
  message="${message}

推奨: メンテナンス枠で次の minor へ段階的にアップグレードしてください（minor の飛ばし上げは不可）。
参考: https://docs.rke2.io/upgrades/manual"
fi

echo "$message"

if [[ "$status" == "ok" ]]; then
  exit 0
fi

if [[ -z "$SLACK_WEBHOOK_URL" ]]; then
  echo "---" >&2
  echo "SLACK_WEBHOOK_URL が未設定のため Slack には送信しませんでした。" >&2
  exit 0
fi

payload=$(jq -n --arg text "$message" '{text: $text}')
curl -fsSL -X POST -H 'Content-Type: application/json' -d "$payload" "$SLACK_WEBHOOK_URL" >/dev/null
echo "Slack に送信しました。" >&2
