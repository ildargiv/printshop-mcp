# printshop-mcp

[English](../../README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · **Português** · [Deutsch](README.de.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Italiano](README.it.md) · [Türkçe](README.tr.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md)

**A gráfica dentro do seu agente de IA.** Peça "crachás para estes 40 convidados, cartões de visita e um flyer": o
agente cria tudo, monta nas folhas, mostra uma prova exata e imprime na **sua impressora de verdade** com precisão
milimétrica. E **lembra todos os seus perfis de impressão**: impressora, papel, bandeja, tipo de mídia, qualidade,
perfil de cor, calibração e até opções exclusivas do fabricante. Explique uma vez e pronto.

<p align="center"><img src="../event-kit-a4-proof.png" width="420" alt="Prova de uma folha A4 mista"></p>

> Status: v0.2, Windows. Novo: imprimir qualquer PDF (por exemplo, de outras skills de design) e imposição automática de muitos itens (`layout`). Em breve: aprendizado com defeitos de impressão, macOS/Linux.

## Instalação

**Claude Code** (skill + servidor MCP em um plugin):

```
/plugin marketplace add ildargiv/printshop-mcp
/plugin install printshop@printshop-mcp
```

**Qualquer cliente MCP** (Claude Desktop, Cursor, Codex...):

```json
{ "mcpServers": { "printshop": { "command": "uvx",
    "args": ["--from", "git+https://github.com/ildargiv/printshop-mcp", "printshop-mcp"] } } }
```

Requer [uv](https://docs.astral.sh/uv/) e Edge ou Chrome (para renderização).

## Por que não Ctrl+P?

| Ctrl+P | printshop-mcp |
|---|---|
| "Ajustar à página" muda a escala sem avisar: 90 mm viram 88,7 mm | Renderização direta em pixels do dispositivo: 1 mm no CSS = 1 mm no papel |
| O conteúdo cai na margem não imprimível | A prova mostra a área não imprimível real; a verificação avisa |
| O agente não vê o resultado | Imagens de prova + relatório JSON: texto cortado, imagens de baixa resolução, papel errado |
| As configurações são esquecidas | Perfis nomeados com o estado completo do driver, calibração e ICC |
| Um tipo de item por impressão | Crachás, cartões e flyers em folhas compartilhadas com marcas de corte |

## O que o agente recebe

- **Skill** `skills/printshop`: fluxo (perfis → design → prova → impressão → ajuste do perfil), regras de HTML,
  referência de imposição e modelos: crachás 90×55, cartões 90×50, flyers A6, prisma de mesa, folha mista.
- **Ferramentas MCP**: `list_printers`, `describe_printer`, `list_profiles`, `save_profile` (`open_driver_dialog=true`
  para definir uma vez as opções do fabricante), `layout`, `proof`, `print_job`, `printer_status`.
- **HTML**: cada folha é `<section class="ps-sheet" style="width:210mm;height:297mm">`, layout em mm;
  `data-fit="9pt"` reduz o texto para caber; `data-cut` adiciona marcas de corte.

## Segurança

Só imprime depois de `proof`; o trabalho expira em 1 hora e é impresso uma vez. `PRINTSHOP_MAX_SHEETS`
(padrão 50) limita o papel; `PRINTSHOP_DRYRUN=1` nunca aciona a impressora.

Licença MIT.
