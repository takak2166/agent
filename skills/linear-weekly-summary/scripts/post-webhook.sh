#!/usr/bin/env bash
set -euo pipefail

# Post Linear weekly summary markdown to a webhook.
#
# Env:
#   LINEAR_WEEKLY_SUMMARY_WEBHOOK_URL   (required unless passed as 2nd arg)
#   LINEAR_WEEKLY_SUMMARY_WEBHOOK_FORMAT  slack | discord | raw  (default: slack)
#
# Usage:
#   post-webhook.sh <markdown-file> [webhook-url]

if [[ $# -lt 1 ]]; then
  echo "Usage: post-webhook.sh <markdown-file> [webhook-url]" >&2
  exit 1
fi

FILE="$1"
URL="${2:-${LINEAR_WEEKLY_SUMMARY_WEBHOOK_URL:-}}"
FORMAT="${LINEAR_WEEKLY_SUMMARY_WEBHOOK_FORMAT:-slack}"

if [[ -z "$URL" ]]; then
  echo "Error: set LINEAR_WEEKLY_SUMMARY_WEBHOOK_URL or pass webhook URL as 2nd argument" >&2
  exit 1
fi

if [[ ! -f "$FILE" ]]; then
  echo "Error: file not found: $FILE" >&2
  exit 1
fi

BODY="$(cat "$FILE")"

case "$FORMAT" in
  slack)
    PAYLOAD="$(jq -n --arg text "$BODY" '{text: $text}')"
    ;;
  discord)
    # Discord limit 2000 chars; truncate with notice if needed
    if [[ ${#BODY} -gt 1900 ]]; then
      BODY="${BODY:0:1900}

...(truncated, see full report in Cursor)"
    fi
    PAYLOAD="$(jq -n --arg content "$BODY" '{content: $content}')"
    ;;
  raw)
    PAYLOAD="$(jq -n --arg body "$BODY" '{body: $body, format: "markdown"}')"
    ;;
  *)
    echo "Error: unknown LINEAR_WEEKLY_SUMMARY_WEBHOOK_FORMAT: $FORMAT" >&2
    exit 1
    ;;
esac

HTTP_CODE="$(curl -sS -o /tmp/linear-weekly-webhook-response.txt -w '%{http_code}' \
  -X POST "$URL" \
  -H 'Content-Type: application/json' \
  -d "$PAYLOAD")"

if [[ "$HTTP_CODE" -lt 200 || "$HTTP_CODE" -ge 300 ]]; then
  echo "Error: webhook returned HTTP $HTTP_CODE" >&2
  cat /tmp/linear-weekly-webhook-response.txt >&2
  exit 1
fi

echo "Posted weekly summary (${#BODY} chars) via $FORMAT webhook (HTTP $HTTP_CODE)"
