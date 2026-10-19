# printshop-mcp

[English](../../README.md) · [Русский](README.ru.md) · **简体中文** · [Español](README.es.md) · [Português](README.pt-BR.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Italiano](README.it.md) · [Türkçe](README.tr.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md)

**AI 智能体里的印刷店。** 只需说"给这 40 位来宾做胸牌，再加名片和一张传单"，智能体就会完成设计、拼版、给你看精确的打印样张，
然后在**你自己的打印机**上以毫米级精度打印出来。它还会**记住你所有的打印配置**：打印机、纸张、纸盒、介质类型、质量、
色彩配置文件、校准，甚至驱动的厂商专有选项。只需说明一次。

<p align="center"><img src="../event-kit-a4-proof.png" width="420" alt="混排 A4 样张"></p>

> 状态：v0.2，Windows。新功能：打印任意 PDF（例如其他设计技能的输出）以及多件物料自动拼版（`layout`）。下一步：从打印问题中自我学习、macOS/Linux。

## 安装

**Claude Code**（技能 + MCP 服务器，一个插件）：

```
/plugin marketplace add ildargiv/printshop-mcp
/plugin install printshop@printshop-mcp
```

**任意 MCP 客户端**（Claude Desktop、Cursor、Codex 等）：

```json
{ "mcpServers": { "printshop": { "command": "uvx",
    "args": ["--from", "git+https://github.com/ildargiv/printshop-mcp", "printshop-mcp"] } } }
```

需要 [uv](https://docs.astral.sh/uv/) 以及 Edge 或 Chrome（用于渲染）。

## 为什么不直接 Ctrl+P？

| Ctrl+P | printshop-mcp |
|---|---|
| "适合页面"会悄悄缩放：90 mm 变成 88.7 mm | 直接渲染到设备像素：CSS 中 1 mm = 纸上 1 mm |
| 内容落入不可打印边距 | 样张显示打印机真实的不可打印区域，预检会发出警告 |
| 智能体看不到结果 | 样张图片 + JSON 报告：文字被截断、图片分辨率低、纸张不对 |
| 每次都要重新设置 | 命名配置，保存完整驱动状态、校准和 ICC |
| 一次只能打一种物料 | 胸牌、名片、传单拼在同一张纸上，带裁切线 |

## 智能体获得什么

- **技能** `skills/printshop`：工作流程（配置 → 设计 → 样张 → 打印 → 修正配置）、HTML 规则、拼版参考和模板：
  胸牌 90×55、名片 90×50、A6 传单、桌牌、混排页。
- **MCP 工具**：`list_printers`、`describe_printer`、`list_profiles`、`save_profile`（`open_driver_dialog=true`
  可在驱动窗口中一次性设置厂商选项）、`layout`、`proof`、`print_job`、`printer_status`。
- **HTML**：每张纸是 `<section class="ps-sheet" style="width:210mm;height:297mm">`，以毫米排版；
  `data-fit="9pt"` 自动缩小文字以适应；`data-cut` 添加裁切线。中文请使用 `"Microsoft YaHei", "Noto Sans CJK SC"` 等字体。

## 安全

必须先生成样张才能打印；任务 1 小时后过期且只能打印一次。`PRINTSHOP_MAX_SHEETS`（默认 50）限制用纸，
`PRINTSHOP_DRYRUN=1` 完全不会触碰打印机。

MIT 许可证。
