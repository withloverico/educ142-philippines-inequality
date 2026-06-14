# Educational Inequality in the Philippines — Data Visualizations

This repository holds the data analysis and figures for our EDUC 142 case study on educational
inequality in the Philippines. We use the **UNESCO World Inequality Database on Education (WIDE)**
as the primary source, supplemented with national tourism statistics and a regional tourism
perception study, to show how schooling outcomes diverge by **household wealth, geography, and
sex**, and to explore tourism-linked early labor-market entry as one possible channel.

`build_charts.py` reproduces all 14 figures from the data in `data/` and `sources/`.

---

## Repository structure

```
.
├── build_charts.py          # one script; regenerates every figure
├── data/
│   ├── phl_wide.csv          # Philippines extract of UNESCO WIDE (the script's main input)
│   └── region_tourism_template.csv  # blank join template for a future regional analysis
├── charts/                  # the 14 rendered PNGs (the deliverable)
├── sources/                 # raw source material (see "Data sources" below)
│   ├── 2000 to 2025 PTSA Statistical Tables_1.xlsx
│   ├── Regional Statatistical Table.xlsx
│   ├── RuralTourism.pdf
│   └── tourism_arrivals/     # DOT visitor-arrival reports, 2008–2023 (context, not plotted)
├── Helvetica-Narrow/        # font — NOT in the repo (see "Fonts")
└── aquarel/                 # styling library — NOT in the repo (see "Styling")
```

> The full 80 MB WIDE source file (`sources/1699460825-wide_2023_sept.csv`) is **not committed**.
> The script reads the small cached extract `data/phl_wide.csv` instead, so the figures reproduce
> without it. To rebuild the extract from scratch, download the global WIDE file (link below) into
> `sources/` and delete `data/phl_wide.csv`; the script will regenerate it.

---

## How to run

```bash
python3 -m pip install pandas matplotlib seaborn openpyxl
# install aquarel + the Helvetica Narrow font (see the two sections below)
python3 build_charts.py
```

This writes the 14 PNGs (and a short `charts/README.md`) into `charts/`.

### Fonts

We render every chart in **Helvetica Narrow** for a compact, editorial look. The font is **not
redistributed here** for licensing reasons. To reproduce the exact typography, place a
`Helvetica-Narrow*.ttf` file in a `Helvetica-Narrow/` folder at the repo root — the script
registers it with Matplotlib under the family name `Helvetica-Narrow`. If the font is missing,
the script falls back to Helvetica Neue / Arial / DejaVu Sans automatically, so it still runs.

### Styling

The charts are themed with **aquarel** (`arctic_light`, a Nord-based theme). We did **not** vendor
the library here — install it separately:

- aquarel: https://github.com/lgienapp/aquarel  (`pip install aquarel`, or clone into `aquarel/`)

The script adds a local `aquarel/` folder to `sys.path` if present, otherwise a pip install works
the same way.

---

## Data sources

| Source | Use | Reference |
|---|---|---|
| UNESCO WIDE (World Inequality Database on Education) | All completion & learning figures | https://www.education-inequalities.org/ |
| Philippine DHS 2003–2017 (via WIDE) | Completion rates by wealth, region, location, sex | PSA & ICF (2018) |
| SEA-PLM 2019 (via WIDE) | Minimum-proficiency (learning) figures | UNICEF & SEAMEO (2020) |
| PSA Philippine Tourism Satellite Accounts | Tourism GDP/employment share (Figs 12–13) | PSA (2025) |
| Supera et al. (2024), *JEFMS* 7(6) | Rural tourism perception survey (Figs 9–10) | doi.org/10.47191/jefms/v7-i6-25 |
| DOT visitor-arrival reports | Background context only (`sources/tourism_arrivals/`) | — |

Full APA citations are kept with the paper draft (not in this repo).

### A note on WIDE column conventions
- Columns ending in `_m` are the survey **estimate** (a share from 0 to 1).
- Columns ending in `_no` are the **sample size** for that estimate.
- The `category` column names the disaggregation (e.g., `Total`, `Wealth`, `Location`, `Sex`,
  `Region`, `Location & Wealth`, `Location & Sex`).

---

## Variables used, by figure

Every figure draws from the columns and breakdowns below. "Completion" variables are
`comp_prim_v2_m` (primary), `comp_lowsec_v2_m` (lower secondary), and `comp_upsec_v2_m` (upper
secondary); "proficiency" variables are `mlevel2_m` (math) and `rlevel2_m` (reading) — the share
reaching SDG minimum proficiency (Level 2).

| # | Figure | Variables (estimate columns) | Breakdown (`category`) | Survey / year |
|---|---|---|---|---|
| 1 | Education funnel | comp_prim / comp_lowsec / comp_upsec | Total | DHS 2017 |
| 2 | Schooling vs. learning | comp_prim, comp_upsec, mlevel2, rlevel2 | Total | DHS 2017 + SEA-PLM 2019 |
| 3 | Wealth gradient in completion | comp_prim / comp_lowsec / comp_upsec | Wealth (Q1–Q5) | DHS 2017 |
| 4 | Rich–poor learning gap | mlevel2, rlevel2 | Wealth | SEA-PLM 2019 |
| 5 | Location × sex | comp_upsec, mlevel2 | Location & Sex | DHS 2017 + SEA-PLM 2019 |
| 6 | Regional ranking | comp_upsec | Region (17 regions) | DHS 2017 |
| 7 | Wealth × location heatmap | comp_upsec | Location & Wealth | DHS 2017 |
| 8 | Wealth gap over time | comp_upsec | Wealth (Q1 vs Q5) | DHS 2003 / 2008 / 2013 / 2017 |
| 9 | Tourism economic impacts | perception means (Table 2) | — | Supera et al. (2024) |
| 10 | Tourism challenges | perception means (Tables 5–6) | — | Supera et al. (2024) |
| 11 | Caraga vs. national | comp_upsec | Region = Caraga vs. Total | DHS 2008–2017 |
| 12 | Tourism economic weight | TDGVA % of GDP (Table 10), employment share (Table 7) | — | PSA PTSA 2000–2024 |
| 13 | National co-trend | tourism employment share + comp_upsec (national) | Total | PSA PTSA + WIDE 2000–2019 |
| 14 | Completion by sex | comp_prim / comp_lowsec / comp_upsec | Sex | DHS 2017 |

A few survey-coverage caveats are handled in code: SEA-PLM 2019 has no estimate for the poorest
wealth quintile, and DHS region names vary across waves, so we standardize on the DHS 2017 naming
for the regional figure. Figures 9–13 are clearly framed as a **co-trend / context only**, not
causal evidence — establishing a tourism–schooling link would require regional tourism and
child-labor data that are not yet available.

---

## How we used aquarel to improve the charts

We started from Matplotlib defaults and layered aquarel's `arctic_light` theme on top to make the
figures publication-ready:

- **Cohesive Nord palette.** `arctic_light` gives a soft off-white background, muted gridlines,
  and trimmed spines, so the data stands out without harsh black axes. We then re-mapped each
  encoding to Nord colors with consistent meaning across all figures — for example, wealth uses a
  red→blue (poorest→richest) ramp, sex uses purple/blue, subjects use orange/green, and island
  groups (Luzon/Visayas/Mindanao) keep one fixed color each. The same variable looks the same in
  every chart.
- **Consistent typography.** On top of the theme we register **Helvetica Narrow** and set bold,
  slightly padded titles, so the 14 figures read as one coherent set rather than 14 one-off plots.
- **Cleaner output.** We render at 200 dpi with tight bounding boxes and a white figure
  background, and add an italic, muted source line under each chart with consistent spacing.

Two practical notes from doing this: the `×` (multiplication) glyph renders blank in Helvetica
Narrow, so we use an ASCII `x` in titles (e.g., "Wealth x Location"); and we disable the themed
grid on the heatmap (Figure 7) so it doesn't bleed over the cells. Both are handled in
`setup_style()` and the individual chart functions in `build_charts.py`.

---

## AI use

We used Claude (Anthropic) as a production assistant to write the figure-generation script, style
the charts, and draft figure captions and citations. The analytical framing, interpretation, and
final writing decisions are our own, and we verified all statistics and citations before use. A
full AI Use Disclosure Statement accompanies the paper.
