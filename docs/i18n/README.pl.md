# printshop-mcp

[English](../../README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Italiano](README.it.md) · [Türkçe](README.tr.md) · **Polski** · [Українська](README.uk.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md)

**Drukarnia w Twoim agencie AI.** Poproś o „identyfikatory dla tych 40 gości, wizytówki i ulotkę”: agent je
zaprojektuje, rozmieści na arkuszach, pokaże dokładny wydruk próbny i wydrukuje na **Twojej prawdziwej drukarce**
z milimetrową dokładnością. I **zapamięta wszystkie Twoje profile drukowania**: drukarkę, papier, podajnik, rodzaj
nośnika, jakość, profil kolorów, kalibrację, a nawet opcje sterownika producenta. Wystarczy wyjaśnić raz.

<p align="center"><img src="../event-kit-a4-proof.png" width="420" alt="Wydruk próbny mieszanego arkusza A4"></p>

> Status: v0.1, Windows. Wkrótce: wejście PDF, automatyczna impozycja mieszana, nauka na błędach druku, macOS/Linux.

## Instalacja

**Claude Code** (skill + serwer MCP w jednej wtyczce):

```
/plugin marketplace add ildargiv/printshop-mcp
/plugin install printshop@printshop-mcp
```

**Dowolny klient MCP** (Claude Desktop, Cursor, Codex…):

```json
{ "mcpServers": { "printshop": { "command": "uvx",
    "args": ["--from", "git+https://github.com/ildargiv/printshop-mcp", "printshop-mcp"] } } }
```

Wymaga [uv](https://docs.astral.sh/uv/) oraz Edge lub Chrome (do renderowania).

## Dlaczego nie Ctrl+P?

| Ctrl+P | printshop-mcp |
|---|---|
| „Dopasuj do strony” po cichu skaluje: 90 mm zmienia się w 88,7 mm | Renderowanie wprost do pikseli urządzenia: 1 mm w CSS = 1 mm na papierze |
| Treść trafia na niezadrukowywalny margines | Wydruk próbny pokazuje prawdziwy obszar niezadrukowywalny, kontrola ostrzega |
| Agent nie widzi efektu | Obrazy próbne + raport JSON: ucięty tekst, obrazy o niskiej rozdzielczości, zły papier |
| Ustawienia za każdym razem giną | Nazwane profile z pełnym stanem sterownika, kalibracją i ICC |
| Jeden rodzaj produktu na wydruk | Identyfikatory, wizytówki i ulotki na wspólnych arkuszach ze znacznikami cięcia |

## Co dostaje agent

- **Skill** `skills/printshop`: przebieg pracy (profile → projekt → wydruk próbny → druk → poprawka profilu), zasady HTML,
  ściąga z impozycji i szablony: identyfikatory 90×55, wizytówki 90×50, ulotki A6, wizytownik stołowy, arkusz mieszany.
- **Narzędzia MCP**: `list_printers`, `describe_printer`, `list_profiles`, `save_profile` (`open_driver_dialog=true`, by
  raz ustawić opcje producenta w oknie sterownika), `proof`, `print_job`, `printer_status`.
- **HTML**: każdy arkusz to `<section class="ps-sheet" style="width:210mm;height:297mm">`, układ w mm;
  `data-fit="9pt"` zmniejsza tekst, aż się zmieści; `data-cut` dodaje znaczniki cięcia.

## Bezpieczeństwo

Druk tylko po `proof`; zadanie wygasa po 1 godzinie i drukuje się raz. `PRINTSHOP_MAX_SHEETS` (domyślnie 50)
ogranicza zużycie papieru; `PRINTSHOP_DRYRUN=1` nigdy nie wysyła nic do drukarki.

Licencja MIT.
