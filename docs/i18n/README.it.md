# printshop-mcp

[English](../../README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · **Italiano** · [Türkçe](README.tr.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md)

**La tipografia dentro il tuo agente IA.** Chiedi «badge per questi 40 ospiti, biglietti da visita e un volantino»:
l’agente li progetta, li impagina sui fogli, ti mostra una prova esatta e li stampa sulla **tua vera stampante** con
precisione millimetrica. E **ricorda tutti i tuoi profili di stampa**: stampante, carta, cassetto, tipo di supporto,
qualità, profilo colore, calibrazione e perfino le opzioni proprietarie del driver. Lo spieghi una volta sola.

<p align="center"><img src="../event-kit-a4-proof.png" width="420" alt="Prova di un foglio A4 misto"></p>

> Stato: v0.2, Windows. Novità: stampa di qualsiasi PDF (ad es. da altre skill di design) e imposizione automatica di molti articoli (`layout`). In arrivo: apprendimento dai difetti di stampa, macOS/Linux.

## Installazione

**Claude Code** (skill + server MCP in un unico plugin):

```
/plugin marketplace add ildargiv/printshop-mcp
/plugin install printshop@printshop-mcp
```

**Qualsiasi client MCP** (Claude Desktop, Cursor, Codex…):

```json
{ "mcpServers": { "printshop": { "command": "uvx",
    "args": ["--from", "git+https://github.com/ildargiv/printshop-mcp", "printshop-mcp"] } } }
```

Richiede [uv](https://docs.astral.sh/uv/) ed Edge o Chrome (per il rendering).

## Perché non Ctrl+P?

| Ctrl+P | printshop-mcp |
|---|---|
| «Adatta alla pagina» riduce senza avvisare: 90 mm diventano 88,7 mm | Rendering diretto nei pixel del dispositivo: 1 mm in CSS = 1 mm su carta |
| Il contenuto finisce nel margine non stampabile | La prova mostra la vera area non stampabile, il controllo avvisa |
| L’agente non vede il risultato | Immagini di prova + report JSON: testo tagliato, immagini a bassa risoluzione, carta sbagliata |
| Le impostazioni si perdono ogni volta | Profili con nome: stato completo del driver, calibrazione e ICC |
| Un solo tipo di articolo per stampa | Badge, biglietti e volantini su fogli condivisi con segni di taglio |

## Cosa riceve l’agente

- **Skill** `skills/printshop`: flusso (profili → impaginazione → prova → stampa → correzione del profilo), regole HTML,
  riferimento di imposizione e modelli: badge 90×55, biglietti 90×50, volantini A6, segnaposto da tavolo, foglio misto.
- **Strumenti MCP**: `list_printers`, `describe_printer`, `list_profiles`, `save_profile` (`open_driver_dialog=true` per
  impostare una volta le opzioni del produttore), `layout`, `proof`, `print_job`, `printer_status`.
- **HTML**: ogni foglio è `<section class="ps-sheet" style="width:210mm;height:297mm">`, layout in mm;
  `data-fit="9pt"` riduce il testo finché entra; `data-cut` aggiunge i segni di taglio.

## Sicurezza

Si stampa solo dopo `proof`; un lavoro scade dopo 1 ora e si stampa una sola volta. `PRINTSHOP_MAX_SHEETS`
(predefinito 50) limita la carta; `PRINTSHOP_DRYRUN=1` non tocca mai la stampante.

Licenza MIT.
