"""
Who are Europe's NEET young people? Motherhood and the gender gap.

Data: European Social Survey Round 11 (2023-24), integrated file, edition 4.2.
The ESS data cannot be redistributed here. Download it (free registration) from
https://ess.sikt.no and place ESS11e04_2.csv in ./data/

Model: weighted logistic regression of NEET status (ages 15-29) with
country fixed effects and standard errors clustered by country.

Run:  python analysis.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
DATA, FIG, RES = HERE / "data", HERE / "figures", HERE / "results"
for p in (FIG, RES):
    p.mkdir(exist_ok=True)

# ---------------------------------------------------------------- 1. sample
ess = pd.read_csv(DATA / "ESS11e04_2.csv", low_memory=False)

# Main activity in the last 7 days (mnactic):
# 1 paid work, 2 education, 7 community/military service  -> not NEET
# 3 unemployed looking, 4 unemployed not looking, 5 sick/disabled,
# 8 housework/looking after children, 9 other               -> NEET
y = ess[ess.agea.between(15, 29) & ess.mnactic.isin([1, 2, 3, 4, 5, 7, 8, 9])].copy()
y["neet"] = y.mnactic.isin([3, 4, 5, 8, 9]).astype(int)

# Household grid: rshipa* = relationship of each household member to respondent
# 1 = partner, 2 = son/daughter
grid = [c for c in ess.columns if c.startswith("rshipa")]
y["child"] = (y[grid] == 2).any(axis=1).astype(int)
y["partner"] = (y[grid] == 1).any(axis=1).astype(int)
y["female"] = (y.gndr == 2).astype(int)
y["abroad"] = (y.brncntr == 2).astype(int)
y["age_c"] = y.agea - 22


def isced3(x):
    """ES-ISCED 1-2 low, 3-5 medium, 6-7 high."""
    return pd.Series(np.select([x.isin([1, 2]), x.isin([3, 4, 5]), x.isin([6, 7])],
                               ["low", "mid", "high"], default="missing"), index=x.index)


y["edu"] = isced3(y.eisced)
parents = y[["eiscedf", "eiscedm"]].where(y[["eiscedf", "eiscedm"]].isin(range(1, 8)))
y["par_edu"] = isced3(parents.max(axis=1)).replace("missing", "unknown")
y = y[y.edu != "missing"]
y["w"] = y.anweight * len(y) / y.anweight.sum()   # analysis weight, normalised

print(f"Sample: {len(y)} young people, {y.cntry.nunique()} countries")

# ---------------------------------------------------------------- 2. model
formula = ("neet ~ female * child + partner + age_c + I(age_c**2)"
           " + C(edu, Treatment('high')) + C(par_edu, Treatment('high'))"
           " + abroad + C(cntry)")
model = smf.glm(formula, y, family=sm.families.Binomial(), var_weights=y.w).fit(
    cov_type="cluster", cov_kwds={"groups": pd.factorize(y.cntry)[0]})


def predicted(female, child):
    """Average predicted probability, setting sex and child status for everyone."""
    z = y.assign(female=female, child=child)
    return np.average(model.predict(z), weights=y.w)


pp = {("Young men, no child at home"): predicted(0, 0),
      ("Young fathers"): predicted(0, 1),
      ("Young women, no child at home"): predicted(1, 0),
      ("Young mothers"): predicted(1, 1)}

mothers_neet = y[(y.female == 1) & (y.child == 1) & (y.neet == 1)]
care_share = np.average(mothers_neet.mnactic == 8, weights=mothers_neet.w)

# ---------------------------------------------------------------- 3. results
keep = [k for k in model.params.index if "cntry" not in k]
ci = model.conf_int().loc[keep]
table = pd.DataFrame({"odds_ratio": np.exp(model.params[keep]),
                      "ci_low": np.exp(ci[0]), "ci_high": np.exp(ci[1]),
                      "p": model.pvalues[keep]}).round(3)
counts = pd.crosstab([y.female.map({0: "men", 1: "women"}), y.child.map({0: "no child", 1: "child"})],
                     y.neet.map({0: "not NEET", 1: "NEET"}))
weighted_rate = y.groupby("female").apply(lambda g: np.average(g.neet, weights=g.w))

md = ["# Results: ESS Round 11 NEET model\n",
      f"Sample: {len(y)} respondents aged 15-29, {y.cntry.nunique()} countries.\n",
      f"Weighted NEET rate: men {weighted_rate[0]:.1%}, women {weighted_rate[1]:.1%}.\n",
      "## Logistic regression (odds ratios; country fixed effects not shown; SEs clustered by country)\n",
      table.to_markdown(),
      "\n## Average predicted probability of being NEET\n",
      pd.Series(pp).mul(100).round(1).to_frame("percent").to_markdown(),
      f"\nShare of NEET young mothers whose main activity is housework/childcare: {care_share:.0%}\n",
      "## Unweighted cell counts\n", counts.to_markdown()]
(RES / "regression_results.md").write_text("\n".join(md))

# ---------------------------------------------------------------- 4. figure
S, T1, T2 = "#fcfcfb", "#0b0b0b", "#52514e"
BLUE, ORANGE, GRID = "#2a78d6", "#eb6834", "#e6e5e0"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": T1})
fig = plt.figure(figsize=(10, 12.5), dpi=130, facecolor=S)
fig.text(0.06, 0.955, "YOUTH NEET IN EUROPE · INDIVIDUAL DATA", fontsize=11.5, color=ORANGE, weight="bold")
fig.text(0.06, 0.935, "It's not being a young woman.", fontsize=24, weight="bold", va="top")
fig.text(0.06, 0.895, "It's being a young mother.", fontsize=24, weight="bold", color=ORANGE, va="top")
fig.text(0.06, 0.835, f"Predicted probability of being NEET, ages 15–29, {y.cntry.nunique()} European countries",
         fontsize=12, color=T2)
ax = fig.add_axes([0.30, 0.33, 0.62, 0.45], facecolor=S)
labels = ["Young men,\nno child at home", "Young fathers", "Young women,\nno child at home", "Young mothers"]
for i, (lab, v) in enumerate(zip(labels, pp.values())):
    yy = len(labels) - 1 - i
    ax.barh(yy, v * 100, height=0.55, color=ORANGE if i == 3 else BLUE)
    ax.text(v * 100 + 1, yy, f"{v*100:.0f}%", va="center", fontsize=18, weight="bold")
ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels[::-1], fontsize=12.5, color=T1)
ax.set_xlim(0, 60); ax.set_xticks([0, 20, 40, 60])
ax.set_xticklabels(["0%", "20%", "40%", "60%"], color=T2)
ax.grid(axis="x", color=GRID); ax.set_axisbelow(True); ax.tick_params(length=0)
for s in ax.spines.values(): s.set_visible(False)
fig.text(0.06, 0.235, f"{care_share:.0%}", fontsize=40, weight="bold", color=ORANGE, va="center")
fig.text(0.25, 0.235, "of NEET young mothers say their main activity\nis housework or looking after children", fontsize=14, va="center", linespacing=1.4)
fig.text(0.06, 0.04, f"Weighted logistic regression, n = {len(y):,}. Controls: age, own education, parental education, partner in\n"
         "household, born abroad, country fixed effects; SEs clustered by country.\n"
         "Source: European Social Survey Round 11 (2023–24).\nAnalysis: Tuğba G. · github.com/tugbasahingunes/neet-europe-analysis",
         fontsize=9.5, color=T2, linespacing=1.5)
fig.savefig(FIG / "neet_young_mothers.png", facecolor=S)
print("Done. See figures/ and results/.")
