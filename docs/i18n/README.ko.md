# printshop-mcp

[English](../../README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [日本語](README.ja.md) · **한국어** · [Italiano](README.it.md) · [Türkçe](README.tr.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md)

**AI 에이전트 안의 인쇄소.** "이 손님 40명의 명찰, 명함, 전단지 한 장"이라고만 말하세요. 에이전트가 디자인하고,
용지에 배치하고, 정확한 교정쇄를 보여 준 다음 **실제 프린터**로 밀리미터 단위까지 정확하게 인쇄합니다.
그리고 **모든 인쇄 프로필을 기억**합니다. 프린터, 용지, 급지함, 용지 종류, 품질, 색상 프로필, 보정값,
제조사 전용 드라이버 옵션까지. 한 번만 설명하면 됩니다.

<p align="center"><img src="../event-kit-a4-proof.png" width="420" alt="혼합 A4 시트 교정쇄"></p>

> 상태: v0.2, Windows. 새 기능: 모든 PDF 인쇄(다른 디자인 스킬의 결과물 등)와 여러 항목 자동 배치(`layout`). 다음 계획: 인쇄 불량으로부터 자가 학습, macOS/Linux.

## 설치

**Claude Code** (스킬 + MCP 서버를 하나의 플러그인으로):

```
/plugin marketplace add ildargiv/printshop-mcp
/plugin install printshop@printshop-mcp
```

**모든 MCP 클라이언트** (Claude Desktop, Cursor, Codex 등):

```json
{ "mcpServers": { "printshop": { "command": "uvx",
    "args": ["--from", "git+https://github.com/ildargiv/printshop-mcp", "printshop-mcp"] } } }
```

[uv](https://docs.astral.sh/uv/)와 렌더링용 Edge 또는 Chrome이 필요합니다.

## 왜 Ctrl+P가 아닌가?

| Ctrl+P | printshop-mcp |
|---|---|
| "페이지에 맞춤"이 몰래 축소: 90 mm가 88.7 mm로 | 장치 픽셀로 직접 렌더링: CSS 1 mm = 종이 1 mm |
| 내용이 인쇄 불가 여백에 들어감 | 교정쇄에 실제 인쇄 불가 영역 표시, 사전 점검이 경고 |
| 에이전트가 결과를 볼 수 없음 | 교정쇄 이미지 + JSON 보고서: 잘린 텍스트, 저해상도 이미지, 잘못된 용지 |
| 매번 설정을 잊음 | 드라이버 전체 상태, 보정, ICC를 담은 이름 있는 프로필 |
| 한 번에 한 종류만 인쇄 | 명찰, 명함, 전단지를 재단선과 함께 한 장에 |

## 에이전트가 얻는 것

- **스킬** `skills/printshop`: 작업 흐름(프로필 → 디자인 → 교정쇄 → 인쇄 → 프로필 수정), HTML 규칙, 배치 참고 자료,
  템플릿: 명찰 90×55, 명함 90×50, A6 전단지, 테이블 텐트, 혼합 시트.
- **MCP 도구**: `list_printers`, `describe_printer`, `list_profiles`, `save_profile`(`open_driver_dialog=true`로
  제조사 옵션을 드라이버 창에서 한 번만 설정), `layout`, `proof`, `print_job`, `printer_status`.
- **HTML**: 각 용지는 `<section class="ps-sheet" style="width:210mm;height:297mm">`, mm 단위 레이아웃.
  `data-fit="9pt"`는 텍스트가 들어갈 때까지 줄이고, `data-cut`은 재단선을 추가합니다. 한국어는 `"Malgun Gothic"` 등의 글꼴을 사용하세요.

## 안전

`proof` 이후에만 인쇄되며, 작업은 1시간 후 만료되고 한 번만 인쇄됩니다. `PRINTSHOP_MAX_SHEETS`(기본 50)로 용지
사용량을 제한하고, `PRINTSHOP_DRYRUN=1`이면 프린터에 아무것도 보내지 않습니다.

MIT 라이선스.
