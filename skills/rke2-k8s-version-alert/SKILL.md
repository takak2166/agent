---
name: rke2-k8s-version-alert
description: Check whether an RKE2 cluster's Kubernetes minor version is approaching or past end-of-life, and draft or send Slack notifications. Use when the user asks about RKE2/k8s version deprecation, EOL, upgrade reminders, or Slack alerts for cluster versions.
---

# RKE2 Kubernetes Version Alert

RKE2 には **k8s バージョン非推奨を Slack に自動通知する組み込み機能はない**。ただし、クラスタのバージョンと公開 EOL 情報を定期的に比較し、Slack Incoming Webhook や GitHub Actions / CronJob で通知する運用は十分現実的。

## 何を「deprecated」とみなすか

| 観点 | 意味 | データソース |
|------|------|--------------|
| **k8s minor EOL** | 上流 Kubernetes のパッチ提供終了。RKE2 も同 minor は EOL 扱い | `https://endoflife.date/api/kubernetes.json` |
| **RKE2 stable との乖離** | 本番向け stable チャンネルより古い minor を使い続けている | `https://update.rke2.io/v1-release/channels` |
| **コンポーネント廃止** | 例: ingress-nginx が v1.37 で削除予定 | [RKE2 release notes](https://docs.rke2.io/release-notes/) |

ユーザーが「k8s のバージョンが deprecated」と言った場合、まず **k8s minor の EOL** を想定し、必要ならコンポーネント廃止も併記する。

## 推奨アーキテクチャ（自宅 RKE2 / Rancher なし）

```text
[定期実行: GitHub Actions cron または k8s CronJob]
        │
        ├─ クラスタ k8s minor を取得 (kubectl / rke2 --version)
        ├─ endoflife.date API で EOL 日を照合
        ├─ (任意) RKE2 stable チャンネルと比較
        └─ 閾値超えなら Slack Incoming Webhook へ POST
```

**Rancher 利用時**は `rancher-monitoring`（Prometheus + Alertmanager）で Slack 連携も可能だが、証明書期限などメトリクスベースのアラート向き。k8s EOL は上記の外部チェックの方が素直。

## エージェントの振る舞い

1. **現状確認**
   - クラスタにアクセスできるか（`kubectl` / SSH）
   - Slack Webhook URL の有無（シークレット名の確認のみ。値は表示・コミットしない）
   - 通知先リポジトリ（例: `my-k8s-platform`）の有無

2. **バージョン取得**（いずれか）
   ```bash
   kubectl version -o json | jq -r '.serverVersion.gitVersion'   # v1.34.9+rke2r1 など
   rke2 --version                                                # ノード上
   ```

3. **EOL 判定**
   - `reference/check-and-notify.sh` を実行、または同等の `curl` + `jq` ロジックを使う
   - デフォルト警告: EOL の **90 日前**（`WARN_DAYS_BEFORE_EOL` で変更可）

4. **Slack 通知**
   - **ユーザーが明示的に送信を依頼した場合のみ** Webhook へ POST する
   - それ以外はメッセージ本文をチャットに提示し、手動送信または CI 組み込みを提案する
   - Webhook URL は GitHub Actions secret（`SLACK_WEBHOOK_URL`）や SOPS 等で管理

5. **恒久運用の提案**
   - 実装先は **`my-k8s-platform`** などインフラ用リポジトリが適切（この `agent` リポジトリはスキル定義用）
   - [TAK-35](https://linear.app/me-time/issue/TAK-35/監視基盤の最小構成を決める) の通知経路決定と整合させる

## 参照スクリプト

`reference/check-and-notify.sh` — ローカルまたは CI から実行:

```bash
# ドライラン（Slack 送信なし）
K8S_VERSION=v1.32.13+rke2r2 ./reference/check-and-notify.sh

# 実送信（Webhook 必須）
K8S_VERSION=v1.32.13+rke2r2 SLACK_WEBHOOK_URL=https://hooks.slack.com/... ./reference/check-and-notify.sh
```

環境変数:

| 変数 | 必須 | 説明 |
|------|------|------|
| `K8S_VERSION` | いずれか | 例: `v1.32.13+rke2r2`。未設定時は `kubectl` を試行 |
| `WARN_DAYS_BEFORE_EOL` | 任意 | デフォルト `90`（日） |
| `SLACK_WEBHOOK_URL` | 送信時 | 未設定ならメッセージを stdout のみ |

## GitHub Actions 例

`reference/github-workflow.example.yml` を `my-k8s-platform` 等にコピーし、以下を設定:

- `schedule`: 例 `0 9 * * 1`（毎週月曜 9:00 UTC）
- `secrets.SLACK_WEBHOOK_URL`
- クラスタ API へのアクセス（`KUBECONFIG` secret または self-hosted runner）

## 出力メッセージ例

```text
⚠️ RKE2/k8s バージョン警告

クラスタ: production
現在: v1.32.13+rke2r2 (Kubernetes 1.32)
EOL: 2026-02-28（あと 42 日）
RKE2 stable: v1.35.6+rke2r1

推奨: 次のメンテナンス枠で 1.33 以降へ段階的にアップグレードしてください。
参考: https://docs.rke2.io/upgrades/manual
```

## 制約

- endoflife.date はコミュニティ API。本番 SLA が必要なら [Kubernetes patch releases](https://kubernetes.io/releases/patch-releases/) や SUSE ライフサイクル表も併記する
- RKE2 は **minor を飛ばすアップグレード不可**（skew policy）。通知文には段階的アップグレードを明記する
- Webhook URL・kubeconfig をリポジトリにコミットしない
