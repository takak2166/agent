# ADR テンプレート

Cosense 保存時は [`storage-cosense.md`](../../product-storage/reference/storage-cosense.md) の行記法に変換する（`#` 見出しは使わない。タイトル行 = `ADR-<NNN>-<slug>`）。

```markdown
# ADR-<NNN>: <短いタイトル>

- **Status**: Proposed | Accepted | Deprecated
- **Date**: YYYY-MM-DD
- **Deciders**: （役割または名前）

## Context

（問題、制約、背景。要件定義へのリンクは保存先内 `[ページタイトル]` で）

## Decision

（採用した設計判断を明確に）

## Options considered

| Option | Pros | Cons |
|--------|------|------|
| A | | |
| B | | |

## Consequences

（正の影響、負の影響、フォローアップ）

## Supersedes / Superseded by

- Supersedes: （なければ None）
- Superseded by: （なければ None。Deprecated 時は後続 ADR の `ADR-NNN` タイトルを記載）
```

`Status` が **Deprecated** のときは **Superseded by** に後続 ADR を必ず入れる（まだ無い場合は Proposed の新 ADR を先に書く）。
