"""
Youth NEET rates across Europe: how much does income explain?

Data: Eurostat (downloaded via the `eurostat` Python package)
  - edat_lfse_20  Young people neither in employment nor in education and training (NEET), 2025
  - tec00114      GDP per capita in PPS (EU27 = 100), 2025
  - edat_lfse_14  Early leavers from education and training, 2025
  - tps00098      Expenditure on social protection, % of GDP, 2024
  - educ_uoe_fine06 Public expenditure on education, % of GDP, 2023

Run:  python analysis.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator

HERE = Path(__file__).parent
DATA, FIG, RES = HERE / "data", HERE / "figures", HERE / "results"
for p in (DATA, FIG, RES):
    p.mkdir(exist_ok=True)


# ---------------------------------------------------------------- 1. data
def load(code):
    """Download a Eurostat table once and cache it as CSV."""
    path = DATA / f"{code}.csv"
    if not path.exists():
        import eurostat
        eurostat.get_data_df(code).to_csv(path, index=False)
    df = pd.read_csv(path)
    return df.rename(columns={"geo\\TIME_PERIOD": "geo"})


def pick(df, year, **filters):
    for col, val in filters.items():
        df = df[df[col] == val]
    s = df.set_index("geo")[year]
    assert s.index.is_unique, filters
    return s


neet_raw = load("edat_lfse_20")
df = pd.DataFrame({
    "neet":   pick(neet_raw, "2025", sex="T", age="Y15-29", wstatus="NEMP"),
    "neet_f": pick(neet_raw, "2025", sex="F", age="Y15-29", wstatus="NEMP"),
    "neet_m": pick(neet_raw, "2025", sex="M", age="Y15-29", wstatus="NEMP"),
    "gdp_pps": pick(load("tec00114"), "2025"),
    "early_leavers": pick(load("edat_lfse_14"), "2025", sex="T", wstatus="POP"),
    "social_prot": pick(load("tps00098"), "2024", spdeps="TOTAL"),
    "edu_spend": pick(load("educ_uoe_fine06"), "2023", isced11="ED02-8"),
})
eu = df.loc["EU27_2020"]
df = df[~df.index.str.match(r"^(EU|EA)")].dropna(subset=["neet", "gdp_pps"])
df["log_gdp"] = np.log(df.gdp_pps)
df.to_csv(DATA / "merged_country_data.csv")
print(f"Countries with NEET + GDP data: {len(df)}")

# ---------------------------------------------------------------- 2. models
lines = []

def report(title, model):
    lines.append(f"\n## {title}\n\nn = {int(model.nobs)}, R² = {model.rsquared:.2f}, "
                 f"adj. R² = {model.rsquared_adj:.2f} (HC3 robust SEs)\n")
    tab = pd.DataFrame({"coef": model.params, "se": model.bse, "p": model.pvalues}).round(3)
    lines.append(tab.to_markdown())

no_tr = df.drop(index="TR")

# Main model: income only, estimated without Türkiye
m_main = smf.ols("neet ~ log_gdp", no_tr).fit(cov_type="HC3")
report("Main model: NEET ~ log GDP per capita (excl. Türkiye)", m_main)

# Robustness: multivariate, with and without Türkiye
f_multi = "neet ~ early_leavers + social_prot + log_gdp"
sub = df.dropna(subset=["early_leavers", "social_prot"])
m_multi = smf.ols(f_multi, sub).fit(cov_type="HC3")
m_multi_nt = smf.ols(f_multi, sub.drop(index="TR")).fit(cov_type="HC3")
report("Robustness: multivariate, all countries", m_multi)
report("Robustness: multivariate, excl. Türkiye", m_multi_nt)

cooks = pd.Series(smf.ols(f_multi, sub).fit().get_influence().cooks_distance[0],
                  index=sub.index).sort_values(ascending=False)
lines.append("\n## Influence check (Cook's distance, multivariate model)\n")
lines.append(cooks.head(5).round(2).to_frame("cooks_d").to_markdown())
lines.append(f"\nTürkiye is a highly influential observation (Cook's D = {cooks['TR']:.2f}). "
             "The early-leavers and social-protection effects are not robust to "
             "excluding it, so only the income relationship is used for the headline.")

# Expected vs actual for Türkiye
m_f = smf.ols("neet_f ~ log_gdp", no_tr).fit()
m_m = smf.ols("neet_m ~ log_gdp", no_tr).fit()
tr = df.loc[["TR"]]
exp_all, exp_f, exp_m = (float(m.predict(tr).iloc[0]) for m in (m_main, m_f, m_m))
lines.append("\n## Türkiye: actual vs expected from income\n")
lines.append(pd.DataFrame({
    "actual": [tr.neet.iloc[0], tr.neet_f.iloc[0], tr.neet_m.iloc[0]],
    "expected": [exp_all, exp_f, exp_m]},
    index=["total", "women", "men"]).round(1).to_markdown())
(RES / "regression_results.md").write_text("# Results: country-level NEET models\n" + "\n".join(lines))

# ---------------------------------------------------------------- 3. figure
S, T1, T2, T3 = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
BLUE, ORANGE, GREY, GRID = "#2a78d6", "#eb6834", "#b5b4ad", "#e6e5e0"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": T1,
                     "axes.labelcolor": T2, "xtick.color": T2, "ytick.color": T2})
trv = tr.iloc[0]
fig = plt.figure(figsize=(10, 12.5), dpi=130, facecolor=S)

# headline
fig.text(0.06, 0.955, "YOUTH NEET IN EUROPE · 2025", fontsize=11.5, color=ORANGE, weight="bold")
fig.text(0.06, 0.935, "Türkiye's NEET rate is twice what\nits income level predicts",
         fontsize=24, weight="bold", va="top", linespacing=1.15)
fig.text(0.06, 0.845, "Share of 15–29-year-olds not in employment, education or training (NEET)",
         fontsize=12, color=T2)

# scatter
ax = fig.add_axes([0.09, 0.47, 0.85, 0.34], facecolor=S)
b0, b1 = m_main.params.iloc[0], m_main.params.iloc[1]
x = np.linspace(np.log(35), np.log(260), 100)
resid_sd = np.sqrt(m_main.scale)
ax.fill_between(np.exp(x), b0 + b1 * x - resid_sd, b0 + b1 * x + resid_sd, color=GREY, alpha=0.18, lw=0, zorder=0)
ax.plot(np.exp(x), b0 + b1 * x, color=GREY, lw=2, zorder=1)
ax.scatter(no_tr.gdp_pps, no_tr.neet, s=75, color=BLUE, edgecolor=S, lw=2, zorder=2)
ax.scatter(tr.gdp_pps, tr.neet, s=170, color=ORANGE, edgecolor=S, lw=2.5, zorder=4)
gx = trv.gdp_pps
ax.annotate("", xy=(gx, trv.neet - 0.8), xytext=(gx, exp_all + 0.6),
            arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=2, mutation_scale=14), zorder=3)
ax.scatter([gx], [exp_all], s=60, facecolor=S, edgecolor=ORANGE, lw=2, zorder=4)
ax.text(gx * 1.04, trv.neet, f"Türkiye  {trv.neet:.0f}%", fontsize=13, weight="bold", va="center")
ax.text(gx * 0.96, exp_all - 1.7, f"expected {exp_all:.0f}%", fontsize=11, color=T2, va="center", ha="right")
labels = {"MK": ("North Macedonia", (8, 2)), "RO": ("Romania", (8, -4)), "IT": ("Italy", (8, 3)),
          "NL": ("Netherlands", (6, -12)), "IE": ("Ireland", (-6, 8)), "LU": ("Luxembourg", (-6, 8)),
          "BA": ("Bosnia & Herz.", (8, -10)), "DE": ("Germany", (6, 6))}
for k, (name, off) in labels.items():
    if k in df.index:
        ax.annotate(name, (df.loc[k, "gdp_pps"], df.loc[k, "neet"]), xytext=off,
                    textcoords="offset points", fontsize=10, color=T3, ha="right" if off[0] < 0 else "left")
ax.set_xscale("log")
ax.xaxis.set_major_locator(FixedLocator([40, 60, 80, 100, 150, 200, 250]))
ax.set_xticklabels(["40", "60", "80", "100", "150", "200", "250"])
ax.xaxis.set_minor_locator(FixedLocator([]))
ax.set_xlabel("GDP per capita in PPS (EU27 = 100, log scale)", fontsize=10.5)
ax.set_ylabel("NEET rate (%)", fontsize=10.5)
ax.set_ylim(0, 30)
ax.grid(axis="y", color=GRID, lw=1); ax.set_axisbelow(True); ax.tick_params(length=0)
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(GRID)
ax.text(0.99, 0.97, f"Trend across {int(m_main.nobs)} European countries (R² = {m_main.rsquared:.2f})",
        transform=ax.transAxes, ha="right", va="top", fontsize=10, color=T2)

# dumbbell by sex
fig.text(0.06, 0.375, "The gap is almost entirely young women", fontsize=16, weight="bold")
fig.text(0.06, 0.352, "Türkiye, expected (from income) vs actual NEET rate", fontsize=11.5, color=T2)
ax2 = fig.add_axes([0.22, 0.14, 0.72, 0.19], facecolor=S)
rows = [("Young women", exp_f, trv.neet_f, ORANGE), ("Young men", exp_m, trv.neet_m, BLUE)]
for i, (lab, e, a, col) in enumerate(rows):
    yy = 1 - i
    ax2.plot([e, a], [yy, yy], color=col, lw=6, alpha=0.35, solid_capstyle="round", zorder=1)
    ax2.scatter([e], [yy], s=160, facecolor=S, edgecolor=T3, lw=2, zorder=2)
    ax2.scatter([a], [yy], s=260, color=col, edgecolor=S, lw=2, zorder=3)
    ax2.text(e, yy + 0.27, f"{e:.0f}%", ha="center", fontsize=11, color=T2)
    ax2.text(a, yy + 0.27, f"{a:.0f}%", ha="center", fontsize=14, weight="bold")
    ax2.text(a + 1.6, yy, f"{a/e:.1f}×", va="center", fontsize=13, color=col, weight="bold")
ax2.set_yticks([1, 0]); ax2.set_yticklabels([r[0] for r in rows], fontsize=12.5, color=T1)
ax2.set_ylim(-0.6, 1.7); ax2.set_xlim(0, 45)
ax2.set_xticks([0, 10, 20, 30, 40]); ax2.set_xticklabels(["0%", "10%", "20%", "30%", "40%"])
ax2.grid(axis="x", color=GRID, lw=1); ax2.set_axisbelow(True); ax2.tick_params(length=0)
for s in ax2.spines.values(): s.set_visible(False)
ax2.scatter([], [], s=80, facecolor=S, edgecolor=T3, lw=2, label="expected")
ax2.scatter([], [], s=80, color=T2, label="actual")
ax2.legend(loc="lower right", frameon=False, fontsize=10.5, ncol=2, bbox_to_anchor=(1, -0.32))

fig.text(0.06, 0.025,
         f"Expected = predicted from GDP per capita (log) using the European trend, estimated without Türkiye. "
         f"Shaded band = ±1 residual SD.\nEU27 NEET 2025: women {eu.neet_f:.0f}%, men {eu.neet_m:.0f}%.  Source: Eurostat (edat_lfse_20, tec00114).\n"
         "Analysis: Tuğba G. · github.com/tugbasahingunes/neet-europe-analysis",
         fontsize=8.8, color=T2, linespacing=1.6)
fig.savefig(FIG / "neet_income_turkiye.png", facecolor=S)
print("Done. See figures/ and results/.")
