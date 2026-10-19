# printshop-mcp

[English](../../README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · **Deutsch** · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Italiano](README.it.md) · [Türkçe](README.tr.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md)

**Die Druckerei in deinem KI-Agenten.** Sag einfach „Namensschilder für diese 40 Gäste, Visitenkarten und einen Flyer“:
Der Agent gestaltet alles, ordnet es auf Bögen an, zeigt dir einen exakten Probedruck und druckt auf **deinem echten
Drucker** – millimetergenau. Und er **merkt sich alle deine Druckprofile**: Drucker, Papier, Fach, Medientyp, Qualität,
Farbprofil, Kalibrierung, sogar herstellerspezifische Treiberoptionen. Einmal erklären, nie wieder.

<p align="center"><img src="../event-kit-a4-proof.png" width="420" alt="Probedruck eines gemischten A4-Bogens"></p>

> Status: v0.2, Windows. Neu: beliebige PDFs drucken (z. B. aus anderen Design-Skills) und automatisches Ausschießen vieler Druckstücke (`layout`). Als Nächstes: Lernen aus Druckfehlern, macOS/Linux.

## Installation

**Claude Code** (Skill + MCP-Server als ein Plugin):

```
/plugin marketplace add ildargiv/printshop-mcp
/plugin install printshop@printshop-mcp
```

**Jeder MCP-Client** (Claude Desktop, Cursor, Codex …):

```json
{ "mcpServers": { "printshop": { "command": "uvx",
    "args": ["--from", "git+https://github.com/ildargiv/printshop-mcp", "printshop-mcp"] } } }
```

Benötigt [uv](https://docs.astral.sh/uv/) und Edge oder Chrome (zum Rendern).

## Warum nicht einfach Strg+P?

| Strg+P | printshop-mcp |
|---|---|
| „An Seite anpassen“ skaliert still: aus 90 mm werden 88,7 mm | Direkt in Gerätepixel gerendert: 1 mm in CSS = 1 mm auf Papier |
| Inhalt landet im nicht bedruckbaren Rand | Der Probedruck zeigt den echten nicht bedruckbaren Bereich, die Prüfung warnt |
| Der Agent sieht das Ergebnis nicht | Probedruck-Bilder + JSON-Bericht: abgeschnittener Text, Bilder mit zu wenig dpi, falsches Papier |
| Einstellungen jedes Mal vergessen | Benannte Profile mit vollständigem Treiberzustand, Kalibrierung und ICC |
| Nur eine Art von Druckstück pro Druck | Namensschilder, Karten und Flyer gemeinsam auf Bögen mit Schnittmarken |

## Was der Agent bekommt

- **Skill** `skills/printshop`: Ablauf (Profile → Gestaltung → Probedruck → Druck → Profil korrigieren), HTML-Regeln,
  Ausschieß-Referenz und Vorlagen: Namensschilder 90×55, Visitenkarten 90×50, A6-Flyer, Tischaufsteller, gemischter Bogen.
- **MCP-Tools**: `list_printers`, `describe_printer`, `list_profiles`, `save_profile` (`open_driver_dialog=true`, um
  Herstelleroptionen einmalig im Treiberfenster festzulegen), `layout`, `proof`, `print_job`, `printer_status`.
- **HTML**: jeder Bogen ist `<section class="ps-sheet" style="width:210mm;height:297mm">`, Layout in mm;
  `data-fit="9pt"` verkleinert Text, bis er passt; `data-cut` setzt Schnittmarken.

## Sicherheit

Gedruckt wird nur nach `proof`; ein Auftrag läuft nach 1 Stunde ab und wird nur einmal gedruckt.
`PRINTSHOP_MAX_SHEETS` (Standard 50) begrenzt den Papierverbrauch; `PRINTSHOP_DRYRUN=1` rührt den Drucker nie an.

MIT-Lizenz.
