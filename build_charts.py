"""
Educational Inequality in the Philippines — 8 visualizations from UNESCO WIDE.

Source data : sources/1699460825-wide_2023_sept.csv (UNESCO World Inequality Database on Education)
Outputs     : data/phl_wide.csv (Philippines extract) + charts/01..14_*.png + charts/README.md

Run: python3 build_charts.py
"""

import glob
import os
import sys
import textwrap

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib import font_manager as fm
import numpy as np
import pandas as pd
import seaborn as sns

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "sources", "1699460825-wide_2023_sept.csv")
EXTRACT = os.path.join(HERE, "data", "phl_wide.csv")
PTSA = os.path.join(HERE, "sources", "2000 to 2025 PTSA Statistical Tables_1.xlsx")
CHARTS = os.path.join(HERE, "charts")
FONT_DIR = os.path.join(HERE, "Helvetica-Narrow")
os.makedirs(CHARTS, exist_ok=True)

# Make the bundled aquarel package importable (not pip-installed)
sys.path.insert(0, os.path.join(HERE, "aquarel"))
from aquarel import load_theme  # noqa: E402

# ----------------------------------------------------------------------------
# Style — aquarel "arctic_light" (Nord) theme + Helvetica Narrow font
# ----------------------------------------------------------------------------
FONT_FAMILY = "DejaVu Sans"  # fallback; replaced by Helvetica-Narrow if registered

# Output directory + theme-aware accent colors. These are reset by setup_style()
# for each theme so the same chart code renders correctly in both light and dark.
OUTDIR = CHARTS
MUTE = "#677693"    # captions / muted bars (light slate on dark, dark slate on light)
ACCENT = "#4C566A"  # reference lines, markers, annotations


def setup_style(theme="arctic_light"):
    """Apply an aquarel arctic theme (light or dark) and the Helvetica Narrow font."""
    global FONT_FAMILY, MUTE, ACCENT
    for f in glob.glob(os.path.join(FONT_DIR, "Helvetica-Narrow*.ttf")):
        fm.fontManager.addfont(f)
        FONT_FAMILY = fm.FontProperties(fname=f).get_name()  # "Helvetica-Narrow"
    load_theme(theme).apply()  # rcParams only; transforms not applied
    dark = theme.endswith("dark")
    # accents that must stay legible against the theme's plot background
    MUTE = "#C8CEDA" if dark else "#677693"
    ACCENT = "#D8DEE9" if dark else "#4C566A"
    plt.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        # match the saved background to the theme so dark charts export dark
        "savefig.facecolor": "#3B4252" if dark else "white",
        "font.family": "sans-serif",
        "font.sans-serif": [FONT_FAMILY, "Helvetica Neue", "Arial", "DejaVu Sans"],
        "axes.titleweight": "bold",
        "axes.titlepad": 14,
        "axes.titlesize": 15,
        "figure.titleweight": "bold",
    })


# Palettes — Nord colors (matched to the arctic_light scheme)
# Polar Night #2E3440 #3B4252 #434C5E #4C566A · Frost #8FBCBB #88C0D0 #81A1C1 #5E81AC
# Aurora #BF616A(red) #D08770(orange) #EBCB8B(yellow) #A3BE8C(green) #B48EAD(purple)
C_LEVEL = {"Primary": "#8FBCBB", "Lower secondary": "#81A1C1", "Upper secondary": "#5E81AC"}
C_SEX = {"Female": "#B48EAD", "Male": "#5E81AC"}
C_SUBJECT = {"Math": "#D08770", "Reading": "#A3BE8C"}
C_RICHPOOR = {"Poorest": "#BF616A", "Richest": "#5E81AC"}
ISLAND_COLORS = {"Luzon": "#5E81AC", "Visayas": "#A3BE8C", "Mindanao": "#D08770"}
NORD = {"red": "#BF616A", "orange": "#D08770", "yellow": "#EBCB8B", "green": "#A3BE8C",
        "purple": "#B48EAD", "frost": "#8FBCBB", "blue": "#5E81AC",
        "ink": "#2E3440", "slate": "#4C566A", "mute": "#677693"}

CAPTION = "Source: UNESCO WIDE (World Inequality Database on Education), {src}"
WEALTH_LABEL = {
    "Quintile 1": "Poorest",
    "Quintile 2": "Q2",
    "Quintile 3": "Q3 (middle)",
    "Quintile 4": "Q4",
    "Quintile 5": "Richest",
}


# ----------------------------------------------------------------------------
# Load Philippines extract (cache to phl_wide.csv)
# ----------------------------------------------------------------------------
def load_phl():
    if os.path.exists(EXTRACT):
        return pd.read_csv(EXTRACT, low_memory=False)
    print("Building Philippines extract from source CSV ...")
    chunks = []
    for chunk in pd.read_csv(SRC, low_memory=False, chunksize=100_000):
        chunks.append(chunk[chunk["country"] == "Philippines"])
    phl = pd.concat(chunks, ignore_index=True)
    phl.to_csv(EXTRACT, index=False)
    print(f"  wrote {EXTRACT}  ({len(phl)} rows)")
    return phl


def add_caption(ax, src, y=-0.12):
    # Placed in axes coordinates so it always clears the x-label / any note above it.
    # Pass a lower (more negative) y on charts that carry a multi-line explanatory note.
    ax.text(0.0, y, CAPTION.format(src=src), transform=ax.transAxes, ha="left",
            va="top", fontsize=10, style="italic", color=MUTE)


def add_caption_raw(ax, text, y=-0.12):
    """Caption without the UNESCO WIDE prefix (for non-WIDE source charts)."""
    ax.text(0.0, y, text, transform=ax.transAxes, ha="left",
            va="top", fontsize=9.5, style="italic", color=MUTE)


def pct_axis(ax, axis="y"):
    fmt = mticker.FuncFormatter(lambda v, _: f"{v*100:.0f}%")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


def save(fig, name):
    path = os.path.join(OUTDIR, name)
    fig.savefig(path)
    plt.close(fig)
    print(f"  saved {name}")
    return path


# ----------------------------------------------------------------------------
# Generic accessor
# ----------------------------------------------------------------------------
def grab(df, survey, year, category, col, sex=None):
    """Return rows for a given survey/year/category breakdown with `col` populated."""
    m = (df["survey"] == survey) & (df["year"] == year) & (df["category"] == category)
    sub = df[m].copy()
    if sex is not None:
        sub = sub[sub["sex"] == sex]
    sub = sub[sub[col].notna()]
    return sub


# ============================================================================
# CHART 1 — National Education Funnel (univariate)
# ============================================================================
def chart1(df):
    t = grab(df, "DHS", 2017, "Total", "comp_prim_v2_m").iloc[0]
    levels = ["Primary", "Lower secondary", "Upper secondary"]
    vals = [t["comp_prim_v2_m"], t["comp_lowsec_v2_m"], t["comp_upsec_v2_m"]]

    fig, ax = plt.subplots(figsize=(11, 6))
    y = np.arange(len(levels))[::-1]
    bars = ax.barh(y, vals, color=[C_LEVEL[l] for l in levels], height=0.62)
    ax.set_yticks(y)
    ax.set_yticklabels(levels)
    ax.set_xlim(0, 1)
    pct_axis(ax, "x")
    for yi, v in zip(y, vals):
        ax.text(v + 0.012, yi, f"{v*100:.0f}%", va="center", fontweight="bold")
    ax.set_xlabel("Share of the relevant age group who completed the level")
    ax.set_title("Education completion by level, Philippines, 2017")
    add_caption(ax, "DHS 2017")
    save(fig, "01_education_funnel.png")


# ============================================================================
# CHART 2 — Schooling vs Learning (univariate national contrast)
# ============================================================================
def chart2(df):
    comp = grab(df, "DHS", 2017, "Total", "comp_prim_v2_m").iloc[0]
    sea = grab(df, "SEA-PLM", 2019, "Total", "mlevel2_m").iloc[0]
    pisa = grab(df, "PISA", 2018, "Total", "mlevel2_m").iloc[0]

    labels = ["Primary\ncompletion", "Upper-sec\ncompletion",
              "Min. math\nproficiency", "Min. reading\nproficiency"]
    vals = [comp["comp_prim_v2_m"], comp["comp_upsec_v2_m"],
            sea["mlevel2_m"], sea["rlevel2_m"]]
    kind = ["Schooling (attainment)", "Schooling (attainment)",
            "Learning (achievement)", "Learning (achievement)"]
    cols = {"Schooling (attainment)": "#5E81AC", "Learning (achievement)": "#BF616A"}

    fig, ax = plt.subplots(figsize=(11, 6.2))
    x = np.arange(len(labels))
    bars = ax.bar(x, vals, color=[cols[k] for k in kind], width=0.62)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1)
    pct_axis(ax, "y")
    for xi, v in zip(x, vals):
        ax.text(xi, v + 0.02, f"{v*100:.0f}%", ha="center", fontweight="bold")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in cols.values()]
    ax.legend(handles, cols.keys(), loc="upper right", frameon=True)
    ax.set_ylabel("Share of children / students")
    ax.set_title("Schooling attainment vs. learning outcomes, Philippines")
    add_caption(ax, "completion DHS 2017; proficiency SEA-PLM 2019 (end of primary)")
    save(fig, "02_schooling_vs_learning.png")


# ============================================================================
# CHART 3 — Wealth gradient in completion (bivariate)
# ============================================================================
def chart3(df):
    w = grab(df, "DHS", 2017, "Wealth", "comp_prim_v2_m").sort_values("wealth")
    order = ["Quintile 1", "Quintile 2", "Quintile 3", "Quintile 4", "Quintile 5"]
    w = w.set_index("wealth").loc[order]
    xlab = [WEALTH_LABEL[q] for q in order]

    fig, ax = plt.subplots(figsize=(11, 6.2))
    x = np.arange(len(order))
    width = 0.26
    series = [("Primary", "comp_prim_v2_m"), ("Lower secondary", "comp_lowsec_v2_m"),
              ("Upper secondary", "comp_upsec_v2_m")]
    for i, (lab, col) in enumerate(series):
        ax.bar(x + (i - 1) * width, w[col].values, width,
               label=lab, color=C_LEVEL[lab])
    ax.set_xticks(x)
    ax.set_xticklabels(xlab)
    ax.set_ylim(0, 1)
    pct_axis(ax, "y")
    ax.set_xlabel("Household wealth quintile")
    ax.set_ylabel("Completion rate")
    ax.legend(title="Education level", loc="lower right")
    ax.set_title("Completion rate by wealth quintile and level, 2017"
                 "")
    add_caption(ax, "DHS 2017")
    save(fig, "03_wealth_gradient_completion.png")


# ============================================================================
# CHART 4 — Rich–poor learning gap (bivariate, SES x learning)
# ============================================================================
def chart4(df):
    order = ["Quintile 1", "Quintile 2", "Quintile 3", "Quintile 4", "Quintile 5"]
    sea = grab(df, "SEA-PLM", 2019, "Wealth", "mlevel2_m").set_index("wealth")
    # reading may be missing for some quintiles; build aligned arrays
    math = [sea.loc[q, "mlevel2_m"] if q in sea.index and pd.notna(sea.loc[q, "mlevel2_m"]) else np.nan for q in order]
    read = [sea.loc[q, "rlevel2_m"] if q in sea.index and pd.notna(sea.loc[q, "rlevel2_m"]) else np.nan for q in order]
    xlab = [WEALTH_LABEL[q] for q in order]

    fig, ax = plt.subplots(figsize=(11, 6.2))
    x = np.arange(len(order))
    width = 0.38
    ax.bar(x - width/2, math, width, label="Math", color=C_SUBJECT["Math"])
    ax.bar(x + width/2, read, width, label="Reading", color=C_SUBJECT["Reading"])
    for xi, (m_, r_) in enumerate(zip(math, read)):
        if not np.isnan(m_):
            ax.text(xi - width/2, m_ + 0.01, f"{m_*100:.0f}%", ha="center", fontsize=12, fontweight="bold")
        if not np.isnan(r_):
            ax.text(xi + width/2, r_ + 0.01, f"{r_*100:.0f}%", ha="center", fontsize=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(xlab)
    ax.set_ylim(0, 0.5)
    pct_axis(ax, "y")
    ax.set_xlabel("Household wealth quintile")
    ax.set_ylabel("Reaching minimum proficiency (Level 2)")
    ax.legend(title="Subject")
    ax.set_title("Minimum proficiency by wealth quintile, end of primary"
                 "")
    ax.text(0.0, -0.16, "Note: SEA-PLM 2019 reports no estimate for the poorest quintile (Q1).",
            transform=ax.transAxes, va="top", fontsize=10, color=MUTE)
    add_caption(ax, "SEA-PLM 2019 (end of primary)", y=-0.21)
    save(fig, "04_richpoor_learning_gap.png")


# ============================================================================
# CHART 5 — Urban-Rural x Gender (multivariate)
# ============================================================================
def chart5(df):
    # Upper-sec completion by Location & Sex (DHS 2017); math proficiency by Location & Sex
    # (SEA-PLM 2019 — full urban/rural x sex coverage; PISA 2018 has no rural estimates)
    comp = grab(df, "DHS", 2017, "Location & Sex", "comp_upsec_v2_m")
    learn = grab(df, "SEA-PLM", 2019, "Location & Sex", "mlevel2_m")

    def cell(frame, col, loc, sex):
        r = frame[(frame["location"] == loc) & (frame["sex"] == sex)]
        return r[col].iloc[0] if len(r) else np.nan

    locs = ["Urban", "Rural"]
    sexes = ["Female", "Male"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.2))
    panels = [
        (axes[0], comp, "comp_upsec_v2_m", "Upper-secondary completion", 1.0, "DHS 2017"),
        (axes[1], learn, "mlevel2_m", "Minimum math proficiency", 0.30, "SEA-PLM 2019"),
    ]
    x = np.arange(len(locs))
    width = 0.38
    for ax, frame, col, title, ymax, src in panels:
        for i, sx in enumerate(sexes):
            vals = [cell(frame, col, loc, sx) for loc in locs]
            ax.bar(x + (i - 0.5) * width, vals, width, label=sx, color=C_SEX[sx])
            for xi, v in zip(x, vals):
                if not np.isnan(v):
                    ax.text(xi + (i - 0.5) * width, v + ymax*0.015, f"{v*100:.0f}%",
                            ha="center", fontsize=11, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(locs)
        ax.set_ylim(0, ymax)
        pct_axis(ax, "y")
        ax.set_title(title, fontsize=15)
        ax.text(0.5, -0.13, src, transform=ax.transAxes, ha="center", fontsize=10, color=MUTE)
    axes[0].legend(title="Sex", loc="lower left")
    fig.suptitle("Completion and learning by location and sex",
                 fontweight="bold", fontsize=18, y=1.02)
    add_caption(axes[0], "DHS 2017 (completion) and SEA-PLM 2019 (learning)", y=-0.17)
    save(fig, "05_urban_rural_gender.png")


# ============================================================================
# CHART 6 — Regional inequality ranking (bivariate, 17 regions)
# ============================================================================
ISLAND = {
    "National Capital": "Luzon", "Cordillera": "Luzon", "Ilocos": "Luzon",
    "Cagayan Valley": "Luzon", "Central Luzon": "Luzon", "Calabarzon": "Luzon",
    "Mimaropa": "Luzon", "Bicol": "Luzon",
    "Western Visayas": "Visayas", "Central Visayas": "Visayas", "Eastern Visayas": "Visayas",
    "Zamboanga Peninsula": "Mindanao", "Northern Mindanao": "Mindanao", "Davao": "Mindanao",
    "Soccsksargen": "Mindanao", "Caraga": "Mindanao",
    "Autonomous Region In Muslim Mindanao": "Mindanao",
}


def chart6(df):
    r = grab(df, "DHS", 2017, "Region", "comp_upsec_v2_m").copy()
    r = r[r["region"].isin(ISLAND.keys())]
    r["island"] = r["region"].map(ISLAND)
    r["label"] = r["region"].replace({
        "Autonomous Region In Muslim Mindanao": "BARMM (ARMM)",
        "National Capital": "NCR (Metro Manila)",
    })
    r = r.sort_values("comp_upsec_v2_m")

    fig, ax = plt.subplots(figsize=(11, 8))
    y = np.arange(len(r))
    ax.barh(y, r["comp_upsec_v2_m"], color=[ISLAND_COLORS[i] for i in r["island"]])
    ax.set_yticks(y)
    ax.set_yticklabels(r["label"])
    ax.set_xlim(0, 1)
    pct_axis(ax, "x")
    for yi, v in zip(y, r["comp_upsec_v2_m"]):
        ax.text(v + 0.008, yi, f"{v*100:.0f}%", va="center", fontsize=11)
    nat = grab(df, "DHS", 2017, "Total", "comp_upsec_v2_m")["comp_upsec_v2_m"].iloc[0]
    ax.axvline(nat, color=ACCENT, ls="--", lw=1.5)
    ax.text(nat + 0.005, 0.2, f"National {nat*100:.0f}%", color=ACCENT, fontsize=11, rotation=90, va="bottom")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in ISLAND_COLORS.values()]
    ax.legend(handles, ISLAND_COLORS.keys(), title="Island group", loc="lower right")
    ax.set_xlabel("Upper-secondary completion rate")
    ax.set_title("Upper-secondary completion by region, 2017")
    add_caption(ax, "DHS 2017")
    save(fig, "06_regional_ranking.png")


# ============================================================================
# CHART 7 — Wealth x Location heatmap (multivariate)
# ============================================================================
def chart7(df):
    order = ["Quintile 1", "Quintile 2", "Quintile 3", "Quintile 4", "Quintile 5"]
    lw = grab(df, "DHS", 2017, "Location & Wealth", "comp_upsec_v2_m")
    mat = pd.DataFrame(index=["Urban", "Rural"], columns=order, dtype=float)
    for _, row in lw.iterrows():
        if row["location"] in mat.index and row["wealth"] in order:
            mat.loc[row["location"], row["wealth"]] = row["comp_upsec_v2_m"]
    mat.columns = [WEALTH_LABEL[q] for q in order]

    fig, ax = plt.subplots(figsize=(11, 5.2))
    sns.heatmap(mat.astype(float) * 100, annot=True, fmt=".0f", cmap="RdYlGn",
                vmin=0, vmax=100, linewidths=2, linecolor="white",
                cbar_kws={"label": "Upper-sec completion (%)"}, ax=ax,
                annot_kws={"fontsize": 14, "fontweight": "bold"})
    ax.grid(False)  # suppress themed axis grid bleeding over the cells
    ax.set_xlabel("Household wealth quintile")
    ax.set_ylabel("Location")
    ax.set_title("Upper-secondary completion by wealth and location, 2017"
                 "")
    add_caption(ax, "DHS 2017")
    save(fig, "07_wealth_location_heatmap.png")


# ============================================================================
# CHART 8 — Wealth gap over time (multivariate / temporal)
# ============================================================================
def chart8(df):
    years = [2003, 2008, 2013, 2017]  # 5-yearly DHS waves (2018 NDHS dropped — overlaps 2017)
    poor, rich = [], []
    for yr in years:
        w = grab(df, "DHS", yr, "Wealth", "comp_upsec_v2_m").set_index("wealth")
        poor.append(w.loc["Quintile 1", "comp_upsec_v2_m"] if "Quintile 1" in w.index else np.nan)
        rich.append(w.loc["Quintile 5", "comp_upsec_v2_m"] if "Quintile 5" in w.index else np.nan)
    poor, rich = np.array(poor, float), np.array(rich, float)

    fig, ax = plt.subplots(figsize=(11, 6.2))
    ax.fill_between(years, poor, rich, color="#EBCB8B", alpha=0.45, label="Poor–rich gap")
    ax.plot(years, rich, "-o", color=C_RICHPOOR["Richest"], lw=3, label="Richest (Q5)")
    ax.plot(years, poor, "-o", color=C_RICHPOOR["Poorest"], lw=3, label="Poorest (Q1)")
    for yr, p, rr in zip(years, poor, rich):
        ax.text(yr, p - 0.04, f"{p*100:.0f}%", ha="center", color=C_RICHPOOR["Poorest"], fontsize=11)
        ax.text(yr, rr + 0.02, f"{rr*100:.0f}%", ha="center", color=C_RICHPOOR["Richest"], fontsize=11)
    # annotate gap at endpoints
    for yr, p, rr in [(years[0], poor[0], rich[0]), (years[-1], poor[-1], rich[-1])]:
        ax.annotate(f"{(rr-p)*100:.0f} pts", xy=(yr, (p+rr)/2), ha="center",
                    fontsize=12, fontweight="bold", color="#D08770")
    ax.set_xticks(years)
    ax.set_ylim(0, 1)
    pct_axis(ax, "y")
    ax.set_xlabel("Survey year")
    ax.set_ylabel("Upper-secondary completion rate")
    ax.legend(loc="center right")
    ax.set_title("Upper-secondary completion, poorest vs. richest, 2003–2017")
    add_caption(ax, "DHS 2003, 2008, 2013, 2017")
    save(fig, "08_wealth_gap_over_time.png")


# ============================================================================
# CONTEXT CHARTS (9–10) — from Supera et al. (2024), Rural Tourism Development
# in the Philippines (JEFMS 7(6)). Perception survey, n=400, Surigao del Norte.
# NOT education outcomes — contextual support for the tourism mechanism only.
# 4-point scale: 1.00–1.74 Low · 1.75–2.49 Moderate · 2.50–3.24 High · 3.25–4.00 Very High
# ============================================================================
TOURISM_NOTE = ("Perception survey (4-pt scale), n=400 stakeholders, 20 municipalities of "
                "Surigao del Norte.\nContextual evidence for the tourism mechanism, not an "
                "education-outcome measure.")
ECON_IMPACT = [  # Table 2 — Perceived economic impact (mean)
    ("New job opportunities created", 3.29),
    ("Attracted outside investors", 3.26),
    ("Raised land / property prices", 3.24),
    ("More business establishments", 3.13),
    ("Income from leasing land/property", 3.12),
    ("Built facilities & infrastructure", 3.02),
    ("Increased local-product output", 3.01),
]
ECON_CHALLENGE = [  # Table 5 (+ key Table 6 item) — Perceived challenges (mean, source)
    ("Poor tourism promotion / advertising", 3.36, 5),
    ("Foreign investors dominate local business", 3.21, 5),
    ("Local business depends on loans for capital", 3.21, 5),
    ("Untrained / unskilled tourism workers", 3.10, 6),   # the human-capital link
    ("Seasonality of tourism business", 3.05, 5),         # the seasonal-work link
    ("Lack of gov't financial / technical support", 2.83, 5),
    ("High local taxation / regulation", 2.68, 5),
    ("Expensive accommodation", 2.47, 5),
]


def _tourism_band(ax):
    ax.axvline(3.25, color="#A3BE8C", ls="--", lw=1.2)
    ax.axvline(2.50, color=MUTE, ls=":", lw=1.0)
    ax.text(3.25, ax.get_ylim()[1], " Very High", color=ACCENT, fontsize=9, va="bottom")


def chart9():
    items = sorted(ECON_IMPACT, key=lambda t: t[1])
    labels = [i[0] for i in items]
    vals = [i[1] for i in items]
    fig, ax = plt.subplots(figsize=(11, 6))
    y = np.arange(len(items))
    colors = ["#D08770" if v >= 3.25 else "#EBCB8B" for v in vals]
    colors[labels.index("New job opportunities created")] = "#BF616A"  # highlight job creation
    ax.barh(y, vals, color=colors)
    ax.set_yticks(y); ax.set_yticklabels(labels)
    ax.set_xlim(1, 4)
    for yi, v in zip(y, vals):
        ax.text(v + 0.03, yi, f"{v:.2f}", va="center", fontweight="bold")
    _tourism_band(ax)
    ax.set_xlabel("Mean perceived impact (1 = none to 4 = very high)")
    ax.set_title("Perceived economic impacts of rural tourism, Surigao del Norte"
                 "")
    add_caption_raw(ax, "Source: Supera et al. (2024), JEFMS 7(6), Table 2. " + TOURISM_NOTE.replace("\n", " "))
    save(fig, "09_tourism_economic_impact.png")


def chart10():
    items = sorted(ECON_CHALLENGE, key=lambda t: t[1])
    labels = [i[0] for i in items]
    vals = [i[1] for i in items]
    bridge = {"Untrained / unskilled tourism workers", "Seasonality of tourism business"}
    colors = ["#BF616A" if labels[i] in bridge else MUTE for i in range(len(labels))]
    fig, ax = plt.subplots(figsize=(11, 6.4))
    y = np.arange(len(items))
    ax.barh(y, vals, color=colors)
    ax.set_yticks(y); ax.set_yticklabels(labels)
    ax.set_xlim(1, 4)
    for yi, v in zip(y, vals):
        ax.text(v + 0.03, yi, f"{v:.2f}", va="center", fontweight="bold")
    _tourism_band(ax)
    handles = [plt.Rectangle((0, 0), 1, 1, color="#BF616A")]
    ax.legend(handles, ["Human-capital and seasonal-labor challenges"],
              loc="lower right", fontsize=11)
    ax.set_xlabel("Mean perceived challenge level (1 = none to 4 = very high)")
    ax.set_title("Perceived challenges of rural tourism, Surigao del Norte"
                 "")
    add_caption_raw(ax, "Source: Supera et al. (2024), JEFMS 7(6), Tables 5–6. " + TOURISM_NOTE.replace("\n", " "))
    save(fig, "10_tourism_challenges.png")


# ============================================================================
# CHART 11 — Geographic spotlight: Caraga (study-area backdrop) over time
# Links the tourism study (Surigao del Norte ⊂ Caraga) to WIDE education data
# by JUXTAPOSITION, not correlation. Caraga is the only honest bridge between
# the two sources (shared geography); the PDF has no time/education dimension.
# ============================================================================
def chart11(df):
    years = [2008, 2013, 2017]
    car, nat = [], []
    for yr in years:
        c = df[(df.survey == "DHS") & (df.year == yr) & (df.category == "Region")
               & (df.region.str.contains("Caraga", na=False))]
        n = grab(df, "DHS", yr, "Total", "comp_upsec_v2_m")
        car.append(c["comp_upsec_v2_m"].iloc[0] if len(c) else np.nan)
        nat.append(n["comp_upsec_v2_m"].iloc[0] if len(n) else np.nan)
    car, nat = np.array(car, float), np.array(nat, float)

    fig, ax = plt.subplots(figsize=(11, 6.2))
    ax.plot(years, nat, "-o", color=ACCENT, lw=3, label="National")
    ax.plot(years, car, "-o", color="#D08770", lw=3, label="Caraga (incl. Surigao del Norte)")
    for yr, c, n in zip(years, car, nat):
        ax.text(yr, c - 0.045, f"{c*100:.0f}%", ha="center", color="#D08770", fontsize=12, fontweight="bold")
        ax.text(yr, n + 0.02, f"{n*100:.0f}%", ha="center", color=ACCENT, fontsize=12)
    ax.set_xticks(years)
    ax.set_ylim(0.4, 0.85)
    pct_axis(ax, "y")
    ax.set_xlabel("DHS survey year")
    ax.set_ylabel("Upper-secondary completion rate")
    ax.legend(loc="upper left")
    ax.set_title("Upper-secondary completion, Caraga vs. national, 2008–2017"
                 "")
    ax.text(0.0, -0.155, "Caraga is the WIDE region containing Surigao del Norte (Supera et al. 2024 study area). "
            "Shown as geographic\ncontext for the tourism work, not a statistical correlation with tourism activity.",
            transform=ax.transAxes, va="top", fontsize=9.5, style="italic", color=MUTE)
    add_caption(ax, "DHS 2008, 2013, 2017", y=-0.24)
    save(fig, "11_caraga_spotlight.png")


# ============================================================================
# PTSA national tourism series (Philippine Tourism Satellite Accounts, PSA)
# ============================================================================
def load_ptsa():
    """Return {'gdp_share': {yr: %}, 'emp_share': {yr: %}} — national, current prices."""
    # Table 10.1: Share of Tourism Direct GVA to GDP (first year-block only)
    d10 = pd.read_excel(PTSA, "Tables 10", header=None)
    start = next(i for i in range(len(d10)) if str(d10.iloc[i, 0]).strip() in ("2000", "2000.0"))
    gdp_share = {}
    for _, r in d10.iloc[start:start + 26].iterrows():
        gdp_share[int(float(r[0]))] = float(r[5])
    # Table 7.1: tourism characteristic industries / total employment
    d7 = pd.read_excel(PTSA, "Table 7", header=None)
    yrs = [int(float(str(y).replace("r", ""))) for y in d7.iloc[3, 1:].tolist()]
    tot = d7.iloc[4, 1:].astype(float).tolist()
    tour = d7.iloc[5, 1:].astype(float).tolist()
    emp_share = {y: 100 * tr / t for y, t, tr in zip(yrs, tot, tour)}
    return {"gdp_share": gdp_share, "emp_share": emp_share}


def nat_completion(df):
    """National upper-sec completion time-series (all surveys), {year: rate}."""
    nat = df[df["category"] == "Total"][["year", "comp_upsec_v2_m"]].dropna()
    # one value per year (prefer the max sample / latest survey — values nearly identical)
    return nat.groupby("year")["comp_upsec_v2_m"].mean().to_dict()


# ============================================================================
# CHART 12 — Tourism's economic weight over time (national, PTSA)
# ============================================================================
def chart12(p):
    yrs = sorted(p["gdp_share"])
    gdp = [p["gdp_share"][y] for y in yrs]
    emp = [p["emp_share"][y] for y in yrs]
    fig, ax = plt.subplots(figsize=(11.5, 6.2))
    ax.plot(yrs, emp, "-o", color="#B48EAD", lw=2.5, ms=4, label="Tourism share of employment")
    ax.plot(yrs, gdp, "-o", color="#A3BE8C", lw=2.5, ms=4, label="Tourism share of GDP (TDGVA)")
    ax.axvspan(2019.5, 2021.5, color="#BF616A", alpha=0.10)
    ax.annotate("COVID-19\ncollapse", xy=(2020, 5), xytext=(2014.5, 3.2),
                fontsize=11, color="#BF616A",
                arrowprops=dict(arrowstyle="->", color="#BF616A"))
    ax.set_ylim(0, 18)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_xlabel("Year")
    ax.set_ylabel("Share of national total")
    ax.legend(loc="upper left")
    ax.set_title("Tourism share of GDP and employment, Philippines, 2000–2025"
                 "")
    ax.text(0.0, -0.16, "Tourism employs a larger share of workers (~15%) than it contributes to GDP (~13% at the "
            "2019 peak), consistent with\nlower-productivity, service-sector work.",
            transform=ax.transAxes, va="top", fontsize=9.5, style="italic", color=MUTE)
    add_caption_raw(ax, "Source: PSA Philippine Tourism Satellite Accounts (PTSA), Tables 7 & 10, current prices.", y=-0.24)
    save(fig, "12_tourism_economic_weight.png")


# ============================================================================
# CHART 13 — National CO-TREND: tourism employment vs schooling (NOT causal)
# ============================================================================
def chart13(p, df):
    comp = nat_completion(df)
    cyrs = sorted(y for y in comp if y <= 2019)
    cvals = [comp[y] * 100 for y in cyrs]
    eyrs = [y for y in sorted(p["emp_share"]) if y <= 2019]
    evals = [p["emp_share"][y] for y in eyrs]

    fig, ax1 = plt.subplots(figsize=(11.5, 6.4))
    l1, = ax1.plot(eyrs, evals, "-o", color="#B48EAD", lw=2.5, ms=4,
                   label="Tourism employment share (PTSA)")
    ax1.set_ylabel("Tourism share of employment", color="#B48EAD")
    ax1.tick_params(axis="y", labelcolor="#B48EAD")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax1.set_ylim(8, 18)

    ax2 = ax1.twinx()
    l2, = ax2.plot(cyrs, cvals, "-s", color="#5E81AC", lw=2.5, ms=5,
                   label="Upper-secondary completion (WIDE)")
    ax2.set_ylabel("Upper-secondary completion rate", color="#5E81AC")
    ax2.tick_params(axis="y", labelcolor="#5E81AC")
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax2.set_ylim(50, 85)

    ax1.set_xlabel("Year")
    ax1.legend(handles=[l1, l2], loc="upper left")
    ax1.set_title("Tourism employment and upper-secondary completion, 2000–2019"
                  "")
    ax1.text(0.0, -0.17,
             "CAUTION: two series that both trend upward over time will always appear 'correlated'. This is a co-trend,\n"
             "not causation, and is confounded by overall economic growth and the K-12 reform (Senior High School, 2016).\n"
             "A regional-level test (tourism intensity vs completion across regions) is needed; this national overlay cannot establish a link.",
             transform=ax1.transAxes, va="top", fontsize=9, style="italic", color="#BF616A")
    add_caption_raw(ax1, "Sources: PSA PTSA (Table 7) and UNESCO WIDE / DHS-Census. Illustrative co-trend only.", y=-0.29)
    save(fig, "13_national_cotrend.png")


# ============================================================================
# CHART 14 — Boys leave earlier: completion by sex across levels (early-labor signal)
# ============================================================================
def chart14(df):
    levels = [("Primary", "comp_prim_v2_m"), ("Lower secondary", "comp_lowsec_v2_m"),
              ("Upper secondary", "comp_upsec_v2_m")]
    f = grab(df, "DHS", 2017, "Sex", "comp_prim_v2_m")
    fem = f[f["sex"] == "Female"].iloc[0]
    mal = f[f["sex"] == "Male"].iloc[0]
    fv = [fem[c] for _, c in levels]
    mv = [mal[c] for _, c in levels]

    fig, ax = plt.subplots(figsize=(11, 6.4))
    x = np.arange(len(levels))
    width = 0.38
    ax.bar(x - width/2, fv, width, label="Female", color=C_SEX["Female"])
    ax.bar(x + width/2, mv, width, label="Male", color=C_SEX["Male"])
    for xi, (fvi, mvi) in enumerate(zip(fv, mv)):
        ax.text(xi - width/2, fvi + 0.012, f"{fvi*100:.0f}%", ha="center", fontsize=11, fontweight="bold")
        ax.text(xi + width/2, mvi + 0.012, f"{mvi*100:.0f}%", ha="center", fontsize=11, fontweight="bold")
        gap = (fvi - mvi) * 100
        ax.annotate(f"−{gap:.0f} pt gap", xy=(xi, max(fvi, mvi) + 0.05), ha="center",
                    fontsize=10.5, fontweight="bold", color=NORD["red"],
                    bbox=dict(boxstyle="round,pad=0.25", fc="#ECEFF4", ec=NORD["red"], lw=0.8))
    ax.set_xticks(x)
    ax.set_xticklabels([l for l, _ in levels])
    ax.set_ylim(0, 1.12)
    pct_axis(ax, "y")
    ax.set_ylabel("Completion rate")
    ax.legend(title="Sex", loc="lower left")
    ax.set_title("Completion by sex and level, 2017"
                 "")
    ax.text(0.0, -0.15, "The female–male completion gap grows from 6 pts (primary) to 12 pts (upper secondary): "
            "consistent with boys being\npulled into early work. Note: a signal, not proof; WIDE does not record reason for leaving.",
            transform=ax.transAxes, va="top", fontsize=9.5, style="italic", color=MUTE)
    add_caption(ax, "DHS 2017", y=-0.23)
    save(fig, "14_boys_leave_earlier.png")


# ----------------------------------------------------------------------------
README = """# Charts — Educational Inequality in the Philippines (UNESCO WIDE)

All figures are generated by `build_charts.py` from the Philippines subset of the
UNESCO WIDE 2023 file. `_m` columns are survey estimates (shares 0–1).

1. **01_education_funnel.png** — Univariate. National completion by level (DHS 2017): the schooling ladder narrows sharply.
2. **02_schooling_vs_learning.png** — Univariate. Attainment vs. achievement: ~90% finish school but <20% reach minimum proficiency.
3. **03_wealth_gradient_completion.png** — Bivariate (SES). Completion rises with wealth; the gap widens at higher levels.
4. **04_richpoor_learning_gap.png** — Bivariate (SES × learning). Minimum math/reading proficiency by wealth quintile.
5. **05_urban_rural_gender.png** — Multivariate. Completion & math proficiency by location × sex; rural boys lag most.
6. **06_regional_ranking.png** — Bivariate (geography). Upper-sec completion across 17 regions, colored by island group.
7. **07_wealth_location_heatmap.png** — Multivariate. Upper-sec completion across wealth × urban/rural — compounding disadvantage.
8. **08_wealth_gap_over_time.png** — Multivariate / temporal. Poorest vs richest completion, 2003–2017; the gap persists.

## Context charts (tourism mechanism — perception data, NOT education outcomes)
Source: Supera et al. (2024), *Rural Tourism Development in the Philippines*, JEFMS 7(6).
Survey of 400 stakeholders in Surigao del Norte. Use only in the motivation/mechanism section.

9. **09_tourism_economic_impact.png** — Job creation is the #1 perceived impact of rural tourism (supports the early-labor-entry premise).
10. **10_tourism_challenges.png** — "Unskilled workers" (3.10) and "seasonality" (3.05) surface as challenges — the bridge to your human-capital argument.
11. **11_caraga_spotlight.png** — Bridges the two sources by geography (not correlation): Caraga (contains Surigao del Norte) upper-sec completion vs national, 2008–2017.

## National tourism series (PSA PTSA — national, not regional)
12. **12_tourism_economic_weight.png** — Tourism share of GDP (~13% peak 2019) and employment (~15%) over 2000–2025; labor-intensive, COVID collapse visible.
13. **13_national_cotrend.png** — Tourism employment vs upper-sec completion, 2000–2019. A co-trend ONLY — explicitly NOT causal (confounded by growth + K-12). The regional scatter remains the real test and needs regional tourism data.
14. **14_boys_leave_earlier.png** — Bivariate (gender). Completion by sex across levels; the female–male gap widens through secondary — the in-data fingerprint of early labor-market entry.

_Styling: aquarel `arctic_light` (Nord) theme, Helvetica Narrow font.
Dark-mode versions of every chart are in `charts/dark/` (aquarel `arctic_dark`)._
"""


def render_all(df, p):
    """Render the full 14-chart set into the current OUTDIR / theme."""
    chart1(df); chart2(df); chart3(df); chart4(df)
    chart5(df); chart6(df); chart7(df); chart8(df)
    chart14(df)
    chart9(); chart10(); chart11(df)
    chart12(p); chart13(p, df)


def main():
    global OUTDIR
    df = load_phl()
    p = load_ptsa()
    # Render the same charts twice: light into charts/, dark into charts/dark/.
    for theme, outdir in [("arctic_light", CHARTS),
                          ("arctic_dark", os.path.join(CHARTS, "dark"))]:
        os.makedirs(outdir, exist_ok=True)
        OUTDIR = outdir
        setup_style(theme)
        print(f"Rendering 14 charts with {theme} -> {outdir}")
        render_all(df, p)
    OUTDIR = CHARTS
    with open(os.path.join(CHARTS, "README.md"), "w") as fh:
        fh.write(README)
    print(f"Done. 14 light + 14 dark PNGs + README in {CHARTS}")


if __name__ == "__main__":
    main()
