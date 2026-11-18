"""
When does the gender gap in youth NEET open up?

Data: Eurostat edat_lfse_20 (EU-LFS), 2025. NEET = neither in employment nor in
education or training, % of the age group, by sex and age (15-24, 25-29).

For each country: gender gap = women's NEET rate minus men's, in percentage points,
for ages 15-24 and 25-29. Descriptive analysis, no modelling.

Run:  python analysis.py
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
DATA, FIG, RES = HERE / "data", HERE / "figures", HERE / "results"
for p in (DATA, FIG, RES):
    p.mkdir(exist_ok=True)
YEAR = "2025"

path = DATA / "edat_lfse_20.csv"
if not path.exists():
    import eurostat
    eurostat.get_data_df("edat_lfse_20").to_csv(path, index=False)
raw = pd.read_csv(path).rename(columns={"geo\\TIME_PERIOD": "geo"})
x = raw[(raw.wstatus == "NEMP") & raw.age.isin(["Y15-24", "Y25-29"])].pivot_table(
    index="geo", columns=["age", "sex"], values=YEAR)

df = pd.DataFrame({
    "f_1524": x[("Y15-24", "F")], "m_1524": x[("Y15-24", "M")],
    "f_2529": x[("Y25-29", "F")], "m_2529": x[("Y25-29", "M")],
}).dropna()
df = df[~df.index.str.match(r"^(EA|EU28)")]
df["gap_1524"] = df.f_1524 - df.m_1524
df["gap_2529"] = df.f_2529 - df.m_2529
NAMES = {"AT": "Austria", "BA": "Bosnia & Herz.", "BE": "Belgium", "BG": "Bulgaria", "CH": "Switzerland",
         "CY": "Cyprus", "CZ": "Czechia", "DE": "Germany", "DK": "Denmark", "EE": "Estonia", "EL": "Greece",
         "ES": "Spain", "FI": "Finland", "FR": "France", "HR": "Croatia", "HU": "Hungary", "IE": "Ireland",
         "IS": "Iceland", "IT": "Italy", "LT": "Lithuania", "LU": "Luxembourg", "LV": "Latvia", "MK": "North Macedonia",
         "MT": "Malta", "NL": "Netherlands", "NO": "Norway", "PL": "Poland", "PT": "Portugal", "RO": "Romania",
         "RS": "Serbia", "SE": "Sweden", "SI": "Slovenia", "SK": "Slovakia", "TR": "Türkiye", "EU27_2020": "EU-27"}
df["name"] = df.index.map(NAMES)
df = df.sort_values("gap_2529")
countries = df.drop(index="EU27_2020")
eu = df.loc["EU27_2020"]
n_widen = int((countries.gap_2529 > countries.gap_1524).sum())

df.round(1).to_csv(RES / "neet_gender_gap_by_age.csv")
(RES / "summary.md").write_text(
    f"# NEET gender gap by age, {YEAR}\n\n"
    f"Countries: {len(countries)} (plus EU-27 aggregate).\n\n"
    f"- EU-27, ages 15-24: women {eu.f_1524:.1f}%, men {eu.m_1524:.1f}% (gap {eu.gap_1524:+.1f} pts)\n"
    f"- EU-27, ages 25-29: women {eu.f_2529:.1f}%, men {eu.m_2529:.1f}% (gap {eu.gap_2529:+.1f} pts)\n"
    f"- The gap is wider at 25-29 than at 15-24 in {n_widen} of {len(countries)} countries.\n"
    f"- Largest gap at 25-29: {countries.gap_2529.idxmax()} ({countries.gap_2529.max():+.1f} pts).\n\n"
    + df.drop(columns="name").round(1).to_markdown())
print(f"Gap widens in {n_widen}/{len(countries)} countries; EU gap {eu.gap_1524:+.1f} -> {eu.gap_2529:+.1f}")

# ---------------------------------------------------------------- figure
S, T1, T2, T3 = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
BLUE, ORANGE, GRID, ZERO = "#2a78d6", "#eb6834", "#e6e5e0", "#b5b4ad"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": T1})
fig = plt.figure(figsize=(10, 13.5), dpi=130, facecolor=S)
fig.text(0.06, 0.962, f"YOUTH NEET IN EUROPE · {YEAR}", fontsize=11.5, color=ORANGE, weight="bold")
fig.text(0.06, 0.945, "Young women and men start out equal.\nBy their late twenties, they don't.",
         fontsize=22, weight="bold", va="top", linespacing=1.18)
fig.text(0.06, 0.872, "Gender gap in NEET rates (women minus men, percentage points)", fontsize=12, color=T2)

ax = fig.add_axes([0.25, 0.10, 0.69, 0.735], facecolor=S)
for i, (code, r) in enumerate(df.iterrows()):
    hl = code in ("TR", "EU27_2020")
    ax.plot([r.gap_1524, r.gap_2529], [i, i], color=ORANGE, lw=3, alpha=0.3, solid_capstyle="round", zorder=1)
    ax.scatter([r.gap_1524], [i], s=55 if not hl else 85, color=BLUE, edgecolor=S, lw=1.5, zorder=2)
    ax.scatter([r.gap_2529], [i], s=70 if not hl else 110, color=ORANGE, edgecolor=S, lw=1.5, zorder=3)
    if hl:
        ax.axhspan(i - 0.45, i + 0.45, color="#f2f1ed", zorder=0)
        ax.text(r.gap_2529 + 1.3, i, f"{r.gap_2529:+.0f}", va="center", fontsize=11, weight="bold")
ax.set_yticks(range(len(df)))
ax.set_yticklabels(df.name, fontsize=10.5, color=T1)
for lab, code in zip(ax.get_yticklabels(), df.index):
    if code in ("TR", "EU27_2020"):
        lab.set_fontweight("bold")
ax.axvline(0, color=ZERO, lw=1.2, zorder=0)
ax.set_xlim(-6, 36); ax.set_ylim(-1.3, len(df) - 0.2)
ax.set_xticks([0, 10, 20, 30]); ax.set_xticklabels(["0", "+10", "+20", "+30 pts"], color=T2)
ax.xaxis.tick_top()
ax.grid(axis="x", color=GRID); ax.set_axisbelow(True); ax.tick_params(length=0)
for s in ax.spines.values(): s.set_visible(False)
ax.text(-0.4, -0.75, "← men higher   women higher →", fontsize=9, color=T3, va="center", ha="center")
ax.scatter([], [], s=70, color=BLUE, label="ages 15–24")
ax.scatter([], [], s=70, color=ORANGE, label="ages 25–29")
ax.legend(loc="lower right", frameon=False, fontsize=11.5, bbox_to_anchor=(1.0, 0.0))

fig.text(0.06, 0.058,
         f"The gap widens between 15–24 and 25–29 in {n_widen} of {len(countries)} countries.  "
         f"EU-27: {abs(eu.gap_1524):.0f} → +{eu.gap_2529:.0f} pts.",
         fontsize=12.5, weight="bold")
fig.text(0.06, 0.02, f"NEET = neither in employment nor in education or training, % of age group.  Source: Eurostat (edat_lfse_20), {YEAR}.\n"
         "Analysis: Tuğba G. · github.com/tugbasahingunes/neet-europe-analysis", fontsize=8.8, color=T2, linespacing=1.6)
fig.savefig(FIG / "neet_gender_gap_by_age.png", facecolor=S)
print("Done.")
