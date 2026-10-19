# printshop-mcp

[English](../../README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Deutsch](README.de.md) · **Français** · [日本語](README.ja.md) · [한국어](README.ko.md) · [Italiano](README.it.md) · [Türkçe](README.tr.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md)

**L’imprimerie dans votre agent IA.** Demandez « des badges pour ces 40 invités, des cartes de visite et un flyer » :
l’agent les conçoit, les impose sur des feuilles, vous montre une épreuve exacte et les imprime sur **votre vraie
imprimante**, au millimètre près. Et il **retient tous vos profils d’impression** : imprimante, papier, bac, type de
support, qualité, profil couleur, calibrage, et même les options propres au fabricant. Expliquez une fois, c’est tout.

<p align="center"><img src="../event-kit-a4-proof.png" width="420" alt="Épreuve d’une feuille A4 mixte"></p>

> Statut : v0.2, Windows. Nouveau : impression de n’importe quel PDF (par exemple issu d’autres skills de design) et imposition automatique de nombreux articles (`layout`). À venir : apprentissage à partir des défauts, macOS/Linux.

## Compatibilité des imprimantes

**Pour les imprimantes papier : jet d’encre, laser, photo, sublimation (objets personnalisés) et étiquettes. Pas pour les imprimantes 3D.**

Fonctionne avec toute imprimante disposant d’un pilote Windows, quelle que soit la marque : l’impression passe par le système d’impression standard de Windows, et les options propres au fabricant (type de papier, sans marge, qualité) sont enregistrées dans les profils via la fenêtre de réglages du pilote.

| Type d’imprimante | Marques |
|---|---|
| Jet d’encre | Epson · Canon · HP · Brother |
| Laser et multifonction | HP · Brother · Canon · Kyocera · Xerox · Ricoh · Konica Minolta · Sharp · Lexmark · OKI · Pantum · Samsung |
| Photo (jet d’encre et sublimation photo) | Epson · Canon · HP · DNP · Mitsubishi · Citizen · Canon Selphy |
| Sublimation (objets personnalisés : mugs, t-shirts, puzzles) | Epson EcoTank / SureColor F (avec encre de sublimation) · Sawgrass · Ricoh |
| Étiquettes / thermique | Zebra · TSC · Brother QL · Dymo · Xprinter |

Vérifié à ce jour:

| Imprimante | Type | Statut |
|---|---|---|
| Microsoft Print to PDF | virtuelle | ✅ tous les tests |
| Epson L8050 | jet d’encre, photo | ✅ bacs, supports et marges détectés · impression test à venir |

Vous avez imprimé avec un autre modèle ? [Signalez-le](https://github.com/ildargiv/printshop-mcp/issues/new?template=printer-report.yml) et il sera ajouté ici. macOS et Linux (CUPS) sont prévus.

## Installation

**Claude Code** (skill + serveur MCP en un seul plugin) :

```
/plugin marketplace add ildargiv/printshop-mcp
/plugin install printshop@printshop-mcp
```

**N’importe quel client MCP** (Claude Desktop, Cursor, Codex…) :

```json
{ "mcpServers": { "printshop": { "command": "uvx",
    "args": ["--from", "git+https://github.com/ildargiv/printshop-mcp", "printshop-mcp"] } } }
```

Nécessite [uv](https://docs.astral.sh/uv/) et Edge ou Chrome (pour le rendu).

## Pourquoi pas Ctrl+P ?

| Ctrl+P | printshop-mcp |
|---|---|
| « Ajuster à la page » réduit sans prévenir : 90 mm deviennent 88,7 mm | Rendu direct en pixels de l’imprimante : 1 mm en CSS = 1 mm sur papier |
| Le contenu tombe dans la marge non imprimable | L’épreuve montre la zone non imprimable réelle, le contrôle avertit |
| L’agent ne voit pas le résultat | Images d’épreuve + rapport JSON : texte coupé, images trop peu définies, mauvais papier |
| Les réglages sont oubliés à chaque fois | Profils nommés avec l’état complet du pilote, le calibrage et l’ICC |
| Un seul type d’article par impression | Badges, cartes et flyers sur des feuilles communes avec traits de coupe |

## Ce que reçoit l’agent

- **Skill** `skills/printshop` : déroulé (profils → mise en page → épreuve → impression → correction du profil), règles
  HTML, référence d’imposition et modèles : badges 90×55, cartes 90×50, flyers A6, chevalet de table, feuille mixte.
- **Outils MCP** : `list_printers`, `describe_printer`, `list_profiles`, `save_profile` (`open_driver_dialog=true` pour
  régler une fois les options du fabricant), `layout`, `proof`, `print_job`, `printer_status`.
- **HTML** : chaque feuille est `<section class="ps-sheet" style="width:210mm;height:297mm">`, mise en page en mm ;
  `data-fit="9pt"` réduit le texte jusqu’à ce qu’il tienne ; `data-cut` ajoute des traits de coupe.

## Sécurité

Impression uniquement après `proof` ; un travail expire au bout d’1 heure et ne s’imprime qu’une fois.
`PRINTSHOP_MAX_SHEETS` (50 par défaut) limite le papier ; `PRINTSHOP_DRYRUN=1` ne touche jamais l’imprimante.

Licence MIT.
