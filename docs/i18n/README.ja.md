# printshop-mcp

[English](../../README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · **日本語** · [한국어](README.ko.md) · [Italiano](README.it.md) · [Türkçe](README.tr.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md)

**AI エージェントの中の印刷所。**「この 40 人分の名札と名刺、チラシを 1 枚」と頼むだけで、エージェントがデザインし、
用紙に面付けし、正確なプルーフを見せてから、**あなたの実際のプリンター**でミリ単位の精度で印刷します。
さらに**すべての印刷プロファイルを記憶**します。プリンター、用紙、給紙トレイ、用紙種類、品質、カラープロファイル、
キャリブレーション、メーカー独自のドライバー設定まで。説明は一度だけで十分です。

<p align="center"><img src="../event-kit-a4-proof.png" width="420" alt="A4 混在シートのプルーフ"></p>

> ステータス：v0.2、Windows。新機能：任意の PDF の印刷（他のデザインスキルの出力など）と、多数のアイテムの自動面付け（`layout`）。今後：印刷不良からの自己学習、macOS/Linux 対応。

## 対応プリンター

**紙に印刷するプリンター用です：インクジェット、レーザー、フォト、昇華型、ラベルプリンター。3D プリンター用ではありません。**

Windows ドライバーがあるプリンターなら、メーカーを問わず使えます。印刷は Windows 標準の印刷システムを通り、メーカー独自の設定（用紙の種類、フチなし、印刷品質）はドライバー自身の設定画面からプロファイルに保存されます。

| プリンターの種類 | メーカー |
|---|---|
| インクジェット | Epson · Canon · HP · Brother |
| レーザー・複合機 | HP · Brother · Canon · Kyocera · Xerox · Ricoh · Konica Minolta · Sharp · Lexmark · OKI · Pantum · Samsung |
| フォト（インクジェット） | Epson · Canon · HP |
| 昇華型（フォト） | DNP · Mitsubishi · Citizen · HiTi · Kodak · Canon Selphy |
| ラベル / サーマル | Zebra · TSC · Brother QL · Dymo · Xprinter |

現在までの検証:

| プリンター | 種類 | 状態 |
|---|---|---|
| Microsoft Print to PDF | 仮想 | ✅ 全テスト合格 |
| Epson L8050 | インクジェット・フォト | ✅ トレイ・用紙種類・余白を認識 · 実機印刷テストはこれから |

別の機種で印刷しましたか？ [報告してください](https://github.com/ildargiv/printshop-mcp/issues/new?template=printer-report.yml)。この一覧に追加します。 macOS と Linux（CUPS）対応を予定しています。

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
  メーカー独自設定をドライバー画面で一度だけ設定）、`layout`、`proof`、`print_job`、`printer_status`。
- **HTML**：各用紙は `<section class="ps-sheet" style="width:210mm;height:297mm">`、レイアウトは mm 単位。
  `data-fit="9pt"` で文字を枠に収まるまで縮小、`data-cut` でトンボを追加。日本語には `"Yu Gothic", "Noto Sans CJK JP"` などのフォントを。

## 安全性

`proof` の後でしか印刷できません。ジョブは 1 時間で失効し、印刷は 1 回だけ。`PRINTSHOP_MAX_SHEETS`（既定 50）で
用紙の使用量を制限、`PRINTSHOP_DRYRUN=1` ならプリンターには一切送信しません。

MIT ライセンス。
