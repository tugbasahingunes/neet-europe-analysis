"""
Youth NEET rates across Europe: how much does income explain?

Data: Eurostat (downloaded via the `eurostat` Python package)
  - edat_lfse_20  Young people neither in employment nor in education and training (NEET), 2024
  - tec00114      GDP per capita in PPS (EU27 = 100), 2024
  - edat_lfse_14  Early leavers from education and training, 2024
  - tps00098      Expenditure on social protection, % of GDP, 2023
  - educ_uoe_fine06 Public expenditure on education, % of GDP, 2022

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
    "neet":   pick(neet_raw, "2024", sex="T", age="Y15-29", wstatus="NEMP"),
    "neet_f": pick(neet_raw, "2024", sex="F", age="Y15-29", wstatus="NEMP"),
    "neet_m": pick(neet_raw, "2024", sex="M", age="Y15-29", wstatus="NEMP"),
    "gdp_pps": pick(load("tec00114"), "2024"),
    "early_leavers": pick(load("edat_lfse_14"), "2024", sex="T", wstatus="POP"),
    "social_prot": pick(load("tps00098"), "2023", spdeps="TOTAL"),
    "edu_spend": pick(load("educ_uoe_fine06"), "2022", isced11="ED02-8"),
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
lines.append("\nTürkiye is a highly influential observation (Cook's D ≈ 1). "
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
S, T1, T2 = "#fcfcfb", "#0b0b0b", "#52514e"
BLUE, ORANGE, GREY, GRID = "#2a78d6", "#eb6834", "#b5b4ad", "#e6e5e0"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": T1,
                     "axes.labelcolor": T2, "xtick.color": T2, "ytick.color": T2})

fig = plt.figure(figsize=(10, 11.5), dpi=130, facecolor=S)
fig.text(0.06, 0.955, "Türkiye's NEET rate is double what its income level predicts —", fontsize=17, weight="bold")
fig.text(0.06, 0.925, "and the gap is almost entirely young women", fontsize=17, weight="bold")
fig.text(0.06, 0.895, "Share of 15–29-year-olds not in employment, education or training (NEET), 2024",
         fontsize=11.5, color=T2)

ax = fig.add_axes([0.08, 0.50, 0.86, 0.35], facecolor=S)
b0, b1 = m_main.params.iloc[0], m_main.params.iloc[1]
x = np.linspace(np.log(35), np.log(250), 100)
ax.plot(np.exp(x), b0 + b1 * x, color=GREY, lw=2, zorder=1)
ax.scatter(no_tr.gdp_pps, no_tr.neet, s=70, color=BLUE, edgecolor=S, lw=2, zorder=2)
ax.scatter(tr.gdp_pps, tr.neet, s=130, color=ORANGE, edgecolor=S, lw=2, zorder=3)
labels = {"TR": ("Türkiye", (8, -4)), "MK": ("North Macedonia", (8, 2)), "RO": ("Romania", (8, -4)),
          "IT": ("Italy", (8, 2)), "NL": ("Netherlands", (6, -12)), "IE": ("Ireland", (-6, 8)),
          "LU": ("Luxembourg", (-6, 8)), "BA": ("Bosnia & Herz.", (8, -10)), "DE": ("Germany", (6, 6))}
for k, (name, off) in labels.items():
    if k in df.index:
        ax.annotate(name, (df.loc[k, "gdp_pps"], df.loc[k, "neet"]), xytext=off,
                    textcoords="offset points", fontsize=10.5, ha="right" if off[0] < 0 else "left",
                    color=T1 if k == "TR" else T2, weight="bold" if k == "TR" else "normal")
gx = tr.gdp_pps.iloc[0]
ax.annotate(f"Expected from income: {exp_all:.0f}%", (gx, b0 + b1 * np.log(gx)), xytext=(gx, 4.5),
            fontsize=10, color=T2, ha="center", arrowprops=dict(arrowstyle="-", color=GREY, lw=1))
ax.set_xscale("log")
ax.xaxis.set_major_locator(FixedLocator([40, 60, 80, 100, 150, 200, 250]))
ax.set_xticklabels(["40", "60", "80", "100", "150", "200", "250"])
ax.xaxis.set_minor_locator(FixedLocator([]))
ax.set_xlabel("GDP per capita in PPS (EU27 = 100, log scale)", fontsize=10.5)
ax.set_ylabel("NEET rate (%)", fontsize=10.5)
ax.set_ylim(0, 30)
ax.grid(axis="y", color=GRID, lw=1); ax.set_axisbelow(True); ax.tick_params(length=0)
for s in ("top", "right"): ax.spines[s].set_visible(False)
for s in ("left", "bottom"): ax.spines[s].set_color(GRID)
ax.text(0.99, 0.97, f"Line: fit across {int(m_main.nobs)} European countries (excl. Türkiye), R² = {m_main.rsquared:.2f}",
        transform=ax.transAxes, ha="right", va="top", fontsize=9.5, color=T2)

fig.text(0.06, 0.405, "Türkiye: actual vs expected NEET rate, by sex", fontsize=13, weight="bold")
ax2 = fig.add_axes([0.22, 0.13, 0.72, 0.25], facecolor=S)
rows = [("Young women", tr.neet_f.iloc[0], exp_f, ORANGE), ("Young men", tr.neet_m.iloc[0], exp_m, BLUE)]
for i, (lab, actual, expected, col) in enumerate(rows):
    y = 1 - i
    ax2.barh(y + 0.17, expected, height=0.3, color=GREY)
    ax2.barh(y - 0.17, actual, height=0.3, color=col)
    ax2.text(expected + 0.6, y + 0.17, f"{expected:.0f}% expected", va="center", fontsize=10.5, color=T2)
    ax2.text(actual + 0.6, y - 0.17, f"{actual:.0f}% actual", va="center", fontsize=11, weight="bold")
ax2.set_yticks([1, 0]); ax2.set_yticklabels([r[0] for r in rows], fontsize=11.5, color=T1)
ax2.set_xlim(0, 48); ax2.set_xticks([0, 10, 20, 30, 40])
ax2.set_xticklabels(["0%", "10%", "20%", "30%", "40%"])
ax2.grid(axis="x", color=GRID, lw=1); ax2.set_axisbelow(True); ax2.tick_params(length=0)
for s in ax2.spines.values(): s.set_visible(False)
fig.text(0.06, 0.045,
         f"Expected = predicted from GDP per capita using the European fit above. "
         f"EU27 NEET: women {eu.neet_f:.0f}%, men {eu.neet_m:.0f}%.\n"
         "Source: Eurostat (edat_lfse_20, tec00114), 2024. Analysis: Tuğba G.",
         fontsize=9.5, color=T2, linespacing=1.5)
fig.savefig(FIG / "neet_income_turkiye.png", facecolor=S)
print("Done. See figures/ and results/.")
