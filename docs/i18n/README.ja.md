# printshop-mcp

[English](../../README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Deutsch](README.de.md) · **日本語**

**AI エージェントの中の印刷所。**「この 40 人分の名札と名刺、チラシを 1 枚」と頼むだけで、エージェントがデザインし、
用紙に面付けし、正確なプルーフを見せてから、**あなたの実際のプリンター**でミリ単位の精度で印刷します。
さらに**すべての印刷プロファイルを記憶**します。プリンター、用紙、給紙トレイ、用紙種類、品質、カラープロファイル、
キャリブレーション、メーカー独自のドライバー設定まで。説明は一度だけで十分です。

<p align="center"><img src="../event-kit-a4-proof.png" width="420" alt="A4 混在シートのプルーフ"></p>

> ステータス：v0.1、Windows。今後：PDF 入力、自動混在面付け、印刷不良からの自己学習、macOS/Linux 対応。

## インストール

**Claude Code**（スキルと MCP サーバーを 1 つのプラグインで）：

```
/plugin marketplace add ildargiv/printshop-mcp
/plugin install printshop@printshop-mcp
```

**任意の MCP クライアント**（Claude Desktop、Cursor、Codex など）：

```json
{ "mcpServers": { "printshop": { "command": "uvx",
    "args": ["--from", "git+https://github.com/ildargiv/printshop-mcp", "printshop-mcp"] } } }
```

[uv](https://docs.astral.sh/uv/) と、レンダリング用に Edge または Chrome が必要です。

## Ctrl+P ではだめな理由

| Ctrl+P | printshop-mcp |
|---|---|
| 「ページに合わせる」が黙って縮小：90 mm が 88.7 mm に | デバイスのピクセルに直接レンダリング：CSS の 1 mm = 紙の 1 mm |
| 内容が印刷できない余白にかかる | プルーフに実際の印刷不可領域を表示し、事前チェックで警告 |
| エージェントには結果が見えない | プルーフ画像と JSON レポート：文字の切れ、低解像度画像、用紙違い |
| 毎回設定を忘れる | ドライバーの全設定・キャリブレーション・ICC を名前付きプロファイルに保存 |
| 1 回の印刷で 1 種類だけ | 名札・名刺・チラシを同じ用紙にトンボ付きで面付け |

## エージェントが得るもの

- **スキル** `skills/printshop`：作業手順（プロファイル → デザイン → プルーフ → 印刷 → プロファイル修正）、HTML ルール、
  面付けリファレンス、テンプレート：名札 90×55、名刺 90×50（日本の名刺 91×55 にも調整可）、A6 チラシ、卓上三角札、混在シート。
- **MCP ツール**：`list_printers`、`describe_printer`、`list_profiles`、`save_profile`（`open_driver_dialog=true` で
  メーカー独自設定をドライバー画面で一度だけ設定）、`proof`、`print_job`、`printer_status`。
- **HTML**：各用紙は `<section class="ps-sheet" style="width:210mm;height:297mm">`、レイアウトは mm 単位。
  `data-fit="9pt"` で文字を枠に収まるまで縮小、`data-cut` でトンボを追加。日本語には `"Yu Gothic", "Noto Sans CJK JP"` などのフォントを。

## 安全性

`proof` の後でしか印刷できません。ジョブは 1 時間で失効し、印刷は 1 回だけ。`PRINTSHOP_MAX_SHEETS`（既定 50）で
用紙の使用量を制限、`PRINTSHOP_DRYRUN=1` ならプリンターには一切送信しません。

MIT ライセンス。
