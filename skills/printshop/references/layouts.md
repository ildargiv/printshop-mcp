# Layout reference

All sizes in mm. "Fits" assumes items edge to edge (shared cut lines) and ~4 mm unprintable border.

## Paper

| Paper | Size |
|---|---|
| A3 | 297 x 420 |
| A4 | 210 x 297 |
| A5 | 148 x 210 |
| A6 | 105 x 148 |
| US Letter | 215.9 x 279.4 |
| US Legal | 215.9 x 355.6 |
| Photo 10x15 (4x6") | 101.6 x 152.4 |

## Common items and how many fit

| Item | Size | Per A4 | Grid on A4 (left, top, columns x rows) |
|---|---|---|---|
| Badge (EU) | 90 x 55 | 10 | 15, 11, 2 x 5 |
| Badge (US 4x3") | 101.6 x 76.2 | 6 | 3.4, 34.2, 2 x 3 (tight: 3.4 mm side margin, check the proof) |
| Business card (EU) | 85 x 55 | 10 | 20, 11, 2 x 5 |
| Business card (RU/CIS) | 90 x 50 | 10 | 15, 23.5, 2 x 5 |
| Business card (US) | 88.9 x 50.8 | 10 | 16.1, 21.5, 2 x 5 |
| Flyer A6 | 105 x 148 | 4 | 0, 0.5, 2 x 2 (keep a 6 mm white frame) |
| Flyer A5 | 148 x 210 | 2 | landscape A4: 0.5, 0, 2 x 1 |
| Place card (folded) | 100 x 70 open 100 x 140 | 4 | 5, 8.5, 2 x 2 |
| Table tent (folded) | 277 x 95 per face | 1 | landscape A4, fold at y = 105 |
| Round sticker | d 50 | 20 | 5, 23.5, 4 x 5 at 50 mm pitch |
| Wristband / strip | 250 x 25 | 8 | landscape A4: 23.5, 5, 1 x 8 |
| Certificate | A4 / A5 | 1 / 2 | full sheet, 10 mm frame |

Centre a grid: left = (sheet_width - columns * item_width) / 2, top = (sheet_height - rows * item_height) / 2.
Check the result is >= 4 mm from every edge.

## Mixed packing recipe (manual; the `layout` tool does this automatically)

1. Group items by profile (paper). One group = its own sheets.
2. Inside a group sort by width. Make columns as wide as the widest item that has many copies
   (on A4: two columns of 90-105 mm, or three of 60-65 mm).
3. Stack items edge to edge down each column; when a column is full start the next.
4. Large items (A6 flyers, 105 wide) take a whole column; fill the space below them with smaller items.
5. Give every item `data-cut`. Report sheets per paper and how many of each item.

Example A4 (event-kit-a4.html):
left column x 10-115: flyer A6 (y 10-158), 2 business cards (y 163-263);
right column x 115-205: 3 badges (y 10-175), 2 business cards (y 175-275).

## Text sizes that read well

| Use | Size |
|---|---|
| Badge name (read at 2 m) | 22-28 pt, `data-fit` min 11 pt |
| Badge role / company | 9-11 pt |
| Business card name | 13-16 pt; details 7.5-9 pt (never below 6.5 pt) |
| Flyer headline A6 | 22-30 pt |
| Table tent name | 48-60 pt, `data-fit` min 24 pt |

## Duplex (front/back)

Not automated yet. Print fronts, put the stack back into the tray, print backs on a separate sheet where the
columns are mirrored left <-> right (long-edge flip). Print a test sheet first and adjust the back side via a
dedicated profile offset if it does not line up.
