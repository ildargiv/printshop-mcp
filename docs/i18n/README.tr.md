# printshop-mcp

[English](../../README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Italiano](README.it.md) · **Türkçe** · [Polski](README.pl.md) · [Українська](README.uk.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md)

**Yapay zekâ ajanınızın içindeki matbaa.** “Bu 40 misafir için yaka kartı, kartvizit ve bir el ilanı” deyin: ajan
hepsini tasarlar, sayfalara yerleştirir, size birebir bir prova gösterir ve **gerçek yazıcınızda** milimetre
hassasiyetiyle basar. Üstelik **tüm baskı profillerinizi hatırlar**: yazıcı, kâğıt, tepsi, ortam türü, kalite, renk
profili, kalibrasyon, hatta üreticiye özel sürücü seçenekleri. Bir kez anlatmanız yeter.

<p align="center"><img src="../event-kit-a4-proof.png" width="420" alt="Karma A4 sayfa provası"></p>

> Durum: v0.1, Windows. Sırada: PDF girişi, otomatik karma yerleşim, baskı hatalarından öğrenme, macOS/Linux.

## Kurulum

**Claude Code** (beceri + MCP sunucusu tek eklentide):

```
/plugin marketplace add ildargiv/printshop-mcp
/plugin install printshop@printshop-mcp
```

**Herhangi bir MCP istemcisi** (Claude Desktop, Cursor, Codex…):

```json
{ "mcpServers": { "printshop": { "command": "uvx",
    "args": ["--from", "git+https://github.com/ildargiv/printshop-mcp", "printshop-mcp"] } } }
```

[uv](https://docs.astral.sh/uv/) ve işleme için Edge veya Chrome gerekir.

## Neden Ctrl+P değil?

| Ctrl+P | printshop-mcp |
|---|---|
| “Sayfaya sığdır” sessizce küçültür: 90 mm, 88,7 mm olur | Doğrudan cihaz piksellerine işlenir: CSS’te 1 mm = kâğıtta 1 mm |
| İçerik basılamayan kenar boşluğuna taşar | Prova gerçek basılamayan alanı gösterir, ön kontrol uyarır |
| Ajan sonucu göremez | Prova görselleri + JSON raporu: kesik metin, düşük çözünürlüklü görsel, yanlış kâğıt |
| Ayarlar her seferinde unutulur | Tam sürücü durumu, kalibrasyon ve ICC içeren adlandırılmış profiller |
| Her baskıda tek tür ürün | Yaka kartı, kartvizit ve el ilanı kesim işaretleriyle aynı sayfada |

## Ajanın elde ettikleri

- **Beceri** `skills/printshop`: iş akışı (profiller → tasarım → prova → baskı → profil düzeltme), HTML kuralları,
  yerleşim rehberi ve şablonlar: yaka kartı 90×55, kartvizit 90×50, A6 el ilanı, masa isimliği, karma sayfa.
- **MCP araçları**: `list_printers`, `describe_printer`, `list_profiles`, `save_profile` (üretici seçeneklerini sürücü
  penceresinde bir kez ayarlamak için `open_driver_dialog=true`), `proof`, `print_job`, `printer_status`.
- **HTML**: her sayfa `<section class="ps-sheet" style="width:210mm;height:297mm">`, yerleşim mm cinsinden;
  `data-fit="9pt"` metni sığana kadar küçültür; `data-cut` kesim işaretleri ekler.

## Güvenlik

Yalnızca `proof` sonrasında basılır; iş 1 saat sonra geçersiz olur ve bir kez basılır. `PRINTSHOP_MAX_SHEETS`
(varsayılan 50) kâğıt kullanımını sınırlar; `PRINTSHOP_DRYRUN=1` yazıcıya hiçbir şey göndermez.

MIT lisansı.
