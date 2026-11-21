"""
Finland and generative AI: who uses it, why, and who works in exposed jobs.

Data
  - Eurostat isoc_ai_iaiu (2025): use of generative AI tools in the last 3 months, % of individuals,
    by age group, sex and purpose.
  - Eurostat isoc_sk_dskl_i21 (2025): basic or above basic overall digital skills (I_DSK2_BAB).
  - Eurostat trng_lfse_01 (2025): participation in education and training in the last 4 weeks, 25-64.
  - Eurostat edat_lfse_03 (2025): tertiary attainment (ISCED 5-8), 25-64.
  - Eurostat tec00114 (2025): GDP per capita in PPS.
  - ESS Round 11 x ILO GenAI classification (as in analyses 05 and 08): Finnish vs European workers.

Methods
  1. Age profiles of GenAI use; youth-adult gap ranking.
  2. Cross-country OLS (HC3) of adult (25-54) GenAI use on digital skills, adult learning,
     tertiary attainment and GDP per capita; leave-one-out predictions; Finland's residual.
  3. Weighted shares of workers by ILO GenAI category, Finland vs other ESS countries,
     with bootstrap 95% intervals.

Run:  python analysis.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

HERE = Path(__file__).parent
DATA, FIG, RES = HERE / "data", HERE / "figures", HERE / "results"


def load(code):
    path = DATA / f"{code}.csv"
    if not path.exists():
        import eurostat
        eurostat.get_data_df(code).to_csv(path, index=False)
    return pd.read_csv(path).rename(columns={"geo\\TIME_PERIOD": "geo"})


AGG = r"^(EU|EA)"
ai = load("isoc_ai_iaiu"); ai = ai[(ai.unit == "PC_IND") & (ai.indic_is == "I_IUAI")]
use = ai.pivot_table(index="geo", columns="ind_type", values="2025")
ages = {"16–24": "Y16_24", "25–34": "Y25_34", "35–44": "Y35_44", "45–54": "Y45_54", "55–64": "Y55_64", "65–74": "Y65_74"}
prof = use[list(ages.values())].rename(columns={v: k for k, v in ages.items()})
work = ai.copy()
purpose = load("isoc_ai_iaiu"); purpose = purpose[(purpose.unit == "PC_IND") & (purpose.ind_type == "IND_TOTAL")]
purpose = purpose.pivot_table(index="geo", columns="indic_is", values="2025")

cty = use.drop(index=[g for g in use.index if pd.Series(g).str.match(AGG).iloc[0]])
gap = (cty.Y16_24 - cty.Y25_54).dropna().sort_values()

# ---------------------------------------------------------------- 2. cross-country model
dsk = load("isoc_sk_dskl_i21")
dsk = dsk[(dsk.indic_is == "I_DSK2_BAB") & (dsk.unit == "PC_IND") & (dsk.ind_type == "Y25_54")].set_index("geo")["2025"]
trn = load("trng_lfse_01"); trn = trn[(trn.sex == "T") & (trn.age == "Y25-64")].set_index("geo")["2025"]
ter = load("edat_lfse_03"); ter = ter[(ter.sex == "T") & (ter.age == "Y25-64") & (ter.isced11 == "ED5-8")].set_index("geo")["2025"]
gdp = load("tec00114").set_index("geo")["2025"]
X = pd.DataFrame({"genai_25_54": cty.Y25_54, "digital_skills": dsk, "adult_learning": trn, "tertiary": ter,
                  "log_gdp": np.log(gdp)}).dropna()
X = X[~X.index.str.match(AGG)]
Z = (X - X.mean()) / X.std()
f = "genai_25_54 ~ digital_skills + adult_learning + tertiary + log_gdp"
m_raw = smf.ols(f, X).fit(cov_type="HC3")
m_std = smf.ols(f, Z).fit(cov_type="HC3")
# leave-one-out predictions
loo = {}
for c in X.index:
    mm = smf.ols(f, X.drop(index=c)).fit()
    loo[c] = float(mm.predict(X.loc[[c]]).iloc[0])
X["loo_pred"] = pd.Series(loo); X["loo_resid"] = X.genai_25_54 - X.loo_pred
loo_r2 = 1 - ((X.genai_25_54 - X.loo_pred) ** 2).sum() / ((X.genai_25_54 - X.genai_25_54.mean()) ** 2).sum()
fi_pred, fi_act = X.loc["FI", "loo_pred"], X.loc["FI", "genai_25_54"]
print(m_std.summary().tables[1]); print("LOO R2", round(loo_r2, 2), "FI", fi_act, round(fi_pred, 1))

# ---------------------------------------------------------------- 3. exposure, Finland vs Europe (ESS x ILO)
occ = pd.read_csv(HERE.parent / "05_genai_exposure_gender" / "data" / "ilo_genai_exposure_isco08_2025.csv")
ess = pd.read_csv(HERE.parent / "02_ess_microdata" / "data" / "ESS11e04_2.csv", low_memory=False,
                  usecols=["cntry", "mnactic", "agea", "isco08", "anweight"])
w = ess[(ess.mnactic == 1) & ess.agea.between(18, 66) & (ess.isco08 < 10000)]
w = w.merge(occ[["ISCO_08", "potential23", "potential25"]], left_on="isco08", right_on="ISCO_08", how="inner")
w["augmentation"] = (w.potential23 == "Augmentation Potential").astype(float)
w["automation"] = (w.potential23 == "Automation Potential").astype(float)
w["highest25"] = w.potential25.str.contains("Gradient 4").astype(float)
w["fi"] = w.cntry == "FI"
rng = np.random.default_rng(5)


def wshare(d, c):
    return np.average(d[c], weights=d.anweight) * 100


exp_rows = {}
for lab, d in (("Finland", w[w.fi]), ("Other ESS countries", w[~w.fi])):
    row = {}
    for c in ("augmentation", "automation", "highest25"):
        est = wshare(d, c)
        bs = [wshare(d.sample(len(d), replace=True, random_state=int(rng.integers(1e9))), c) for _ in range(500)]
        row[c] = est; row[c + "_lo"], row[c + "_hi"] = np.percentile(bs, [2.5, 97.5])
    row["n"] = len(d)
    exp_rows[lab] = row
expo = pd.DataFrame(exp_rows).T
print(expo.round(1))

# ---------------------------------------------------------------- results
(RES / "results.md").write_text(
    "# Results: Finland and generative AI\n\n"
    "## GenAI use by age, 2025 (% of individuals, Eurostat isoc_ai_iaiu)\n\n"
    + prof.loc[["FI", "EU27_2020", "SE", "DK", "NO", "EE"]].round(1).to_markdown()
    + "\n\n## Purposes of use, all individuals 16-74 (%)\n\n"
    + purpose.loc[["FI", "EU27_2020"], ["I_IUAI", "I_IUAIWP", "I_IUAIPR", "I_IUAIFE"]].round(1).to_markdown()
    + f"\n\n## Youth (16-24) minus adults (25-54), percentage points: {len(gap)} countries\n\n"
    + gap.round(1).to_frame("gap_pts").to_markdown()
    + f"\n\n## Cross-country model of GenAI use among 25-54-year-olds (n = {len(X)} countries, HC3 SEs)\n\n"
    "Standardised coefficients:\n\n" + pd.DataFrame({"beta": m_std.params, "se": m_std.bse, "p": m_std.pvalues}).round(3).to_markdown()
    + f"\n\nR² = {m_raw.rsquared:.2f}; leave-one-out R² = {loo_r2:.2f}. Finland: actual {fi_act:.1f}%, "
      f"predicted (leave-one-out) {fi_pred:.1f}%.\n\n"
    + X.sort_values("loo_resid").round(1).to_markdown()
    + "\n\n## Workers by ILO GenAI category (ESS Round 11), weighted %, bootstrap 95% CI\n\n" + expo.round(1).to_markdown())
pd.to_pickle(dict(prof=prof, purpose=purpose, gap=gap, X=X, m_std=m_std, m_raw=m_raw, loo_r2=loo_r2, expo=expo), RES / "_cache.pkl")
print("saved")

# ---------------------------------------------------------------- figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
S, T1, T2, T3 = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
BLUE, ORANGE, GREY, GRID, LIGHT, FIN = "#2a78d6", "#eb6834", "#b5b4ad", "#e6e5e0", "#f2f1ed", "#1f4fa3"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": T1})
fig = plt.figure(figsize=(10, 13.5), dpi=130, facecolor=S)
fig.text(0.06, 0.962, "FINLAND · GENERATIVE AI · 2025", fontsize=11.5, color=FIN, weight="bold")
fig.text(0.06, 0.945, "In Finland, generative AI isn't just\nfor the young", fontsize=23, weight="bold", va="top", linespacing=1.18)
fig.text(0.06, 0.873, "Share of people who used generative AI tools in the last 3 months (Eurostat, 2025)", fontsize=11.5, color=T2)

# panel 1: age profile
fig.text(0.06, 0.835, "1  Use by age: Finland vs EU-27", fontsize=14.5, weight="bold")
ax1 = fig.add_axes([0.08, 0.60, 0.50, 0.215], facecolor=S)
xs = np.arange(len(prof.columns))
for code, col, lab, lw in (("EU27_2020", GREY, "EU-27", 2.5), ("FI", FIN, "Finland", 3.5)):
    ax1.plot(xs, prof.loc[code].values, color=col, lw=lw, marker="o", ms=6, label=lab)
i45 = list(prof.columns).index("45–54")
ax1.annotate(f"{prof.loc['FI','45–54']:.0f}%", (i45, prof.loc["FI", "45–54"]), xytext=(6, 8), textcoords="offset points", fontsize=12, weight="bold", color=FIN)
ax1.annotate(f"{prof.loc['EU27_2020','45–54']:.0f}%", (i45, prof.loc["EU27_2020", "45–54"]), xytext=(6, -16), textcoords="offset points", fontsize=12, color=T2)
ax1.set_xticks(xs); ax1.set_xticklabels(prof.columns, fontsize=10.5)
ax1.set_ylim(0, 75); ax1.set_yticks([0, 25, 50, 75]); ax1.set_yticklabels(["0%", "25%", "50%", "75%"], fontsize=10, color=T2)
ax1.grid(axis="y", color=GRID); ax1.set_axisbelow(True); ax1.tick_params(length=0)
for s_ in ("top", "right", "left"): ax1.spines[s_].set_visible(False)
ax1.spines["bottom"].set_color(GRID)
ax1.legend(frameon=False, fontsize=11, loc="upper right")
fig.text(0.62, 0.80, f"Among 45–54-year-olds,\nFinns use generative AI\nalmost twice as often\nas the EU average.", fontsize=12, va="top", linespacing=1.45)
fi_gap, eu_gap = gap["FI"], use.loc["EU27_2020", "Y16_24"] - use.loc["EU27_2020", "Y25_54"]
fig.text(0.62, 0.69, f"Gap between young people\n(16–24) and adults (25–54):", fontsize=11, color=T2, va="top", linespacing=1.4)
fig.text(0.62, 0.635, f"{fi_gap:.0f} pts", fontsize=24, weight="bold", color=FIN, va="top")
fig.text(0.80, 0.635, f"{eu_gap:.0f} pts", fontsize=24, weight="bold", color=GREY, va="top")
fig.text(0.62, 0.598, f"Finland: smallest\nof {len(gap)} countries", fontsize=10, color=T1, va="top", linespacing=1.3)
fig.text(0.80, 0.598, "EU-27", fontsize=10, color=T2, va="top")

# panel 2: why — digital skills scatter
fig.text(0.06, 0.545, "2  What explains it? Skills, not age", fontsize=14.5, weight="bold")
ax2 = fig.add_axes([0.09, 0.30, 0.48, 0.225], facecolor=S)
oth = X.drop(index="FI")
ax2.scatter(oth.digital_skills, oth.genai_25_54, s=55, color=GREY, edgecolor=S, lw=1.5)
ax2.scatter(X.loc["FI", "digital_skills"], X.loc["FI", "genai_25_54"], s=140, color=FIN, edgecolor=S, lw=2, zorder=3)
ax2.annotate("Finland", (X.loc["FI", "digital_skills"], X.loc["FI", "genai_25_54"]), xytext=(-8, 8), textcoords="offset points", ha="right", fontsize=11.5, weight="bold", color=FIN)
b = np.polyfit(X.digital_skills, X.genai_25_54, 1); xx = np.linspace(X.digital_skills.min(), X.digital_skills.max(), 50)
ax2.plot(xx, np.polyval(b, xx), color=T3, lw=1.5, ls=(0, (4, 3)))
ax2.set_xlabel("Adults with at least basic digital skills (%)", fontsize=10, color=T2)
ax2.set_ylabel("GenAI use, ages 25–54 (%)", fontsize=10, color=T2)
ax2.tick_params(length=0, labelsize=9.5, colors=T2); ax2.grid(color=GRID); ax2.set_axisbelow(True)
for s_ in ax2.spines.values(): s_.set_visible(False)
coef = m_std.params
fig.text(0.62, 0.52, f"Across {len(X)} European countries, adult digital\nskills and university education explain\nabout two thirds of the differences in\nadult GenAI use (leave-one-out R² {loo_r2:.2f}).",
         fontsize=10.8, va="top", linespacing=1.45)
fig.text(0.62, 0.405, f"Finland sits close to the line: the model\npredicts {X.loc['FI','loo_pred']:.0f}%, actual {X.loc['FI','genai_25_54']:.0f}%.\nHigh use is what high skills look like.",
         fontsize=10.8, va="top", linespacing=1.45, weight="bold")

# panel 3: exposure
fig.text(0.06, 0.245, "3  And fewer Finnish workers are in the most exposed jobs", fontsize=14.5, weight="bold")
fig.text(0.06, 0.224, "Share of workers by ILO generative AI category (ESS 2023–24 × ILO classification)", fontsize=10.5, color=T2)
items = [("AI can support the work (ILO 2023)", "augmentation"), ("Most exposed jobs (ILO 2025, Gradient 4)", "highest25")]
for i, (lab, k) in enumerate(items):
    x0 = 0.06 + i * 0.46
    fig.text(x0, 0.19, lab, fontsize=11.5, color=T2, va="top")
    fig.text(x0, 0.16, f"{expo.loc['Finland', k]:.1f}%", fontsize=26, weight="bold", color=FIN, va="top")
    fig.text(x0 + 0.17, 0.16, f"{expo.loc['Other ESS countries', k]:.1f}%", fontsize=26, weight="bold", color=GREY, va="top")
    fig.text(x0, 0.115, "Finland", fontsize=10, color=FIN, va="top"); fig.text(x0 + 0.17, 0.115, "Other ESS countries", fontsize=10, color=T2, va="top")

fig.text(0.06, 0.02,
         "Sources: Eurostat isoc_ai_iaiu, isoc_sk_dskl_i21, trng_lfse_01, edat_lfse_03, tec00114 (2025); European Social Survey Round 11;\n"
         f"ILO generative AI occupational classification (Gmyrek et al. 2023/2025). Cross-country OLS with HC3 SEs, n = {len(X)}.\n"
         f"Finnish workers n = {int(expo.loc['Finland','n'])}; 95% bootstrap intervals in the repository. Analysis: Tuğba G. · github.com/tugbasahingunes/neet-europe-analysis",
         fontsize=8.2, color=T2, linespacing=1.6)
fig.savefig(FIG / "finland_genai.png", facecolor=S)
print("figure done")
