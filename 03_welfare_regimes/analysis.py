"""
Does the motherhood gap in youth NEET differ across European welfare regimes?

Data: European Social Survey Round 11 (2023-24). Place ESS11e04_2.csv in
../02_ess_microdata/data/ (see that folder's README).

Sample: women aged 15-29 in 26 countries grouped into five welfare regimes
(Israel, Montenegro, Serbia and Ukraine are excluded: no standard regime).
For each regime, a weighted logistic regression of NEET status on having a
child at home, with the same controls as analysis 02 and country fixed effects.
Gap = average predicted probability (mother) - (no child at home).
95% intervals from 300 bootstrap resamples.

Run:  python analysis.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
DATA = HERE.parent / "02_ess_microdata" / "data"
FIG, RES = HERE / "figures", HERE / "results"
for p in (FIG, RES):
    p.mkdir(exist_ok=True)

REGIMES = {
    "Nordic": ["SE", "NO", "FI", "IS"],
    "Continental": ["AT", "BE", "CH", "DE", "FR", "NL"],
    "Liberal": ["GB", "IE"],
    "Southern": ["ES", "IT", "PT", "GR", "CY"],
    "Central & Eastern": ["BG", "HR", "EE", "HU", "LT", "LV", "PL", "SI", "SK"],
}

# ---------------------------------------------------------------- sample (as in 02)
ess = pd.read_csv(DATA / "ESS11e04_2.csv", low_memory=False)
y = ess[ess.agea.between(15, 29) & ess.mnactic.isin([1, 2, 3, 4, 5, 7, 8, 9])].copy()
y["neet"] = y.mnactic.isin([3, 4, 5, 8, 9]).astype(int)
grid = [c for c in ess.columns if c.startswith("rshipa")]
y["child"] = (y[grid] == 2).any(axis=1).astype(int)
y["partner"] = (y[grid] == 1).any(axis=1).astype(int)
y["abroad"] = (y.brncntr == 2).astype(int)
y["age_c"] = y.agea - 22


def isced3(x):
    return pd.Series(np.select([x.isin([1, 2]), x.isin([3, 4, 5]), x.isin([6, 7])],
                               ["low", "mid", "high"], default="missing"), index=x.index)


y["edu"] = isced3(y.eisced)
parents = y[["eiscedf", "eiscedm"]].where(y[["eiscedf", "eiscedm"]].isin(range(1, 8)))
y["par_edu"] = isced3(parents.max(axis=1)).replace("missing", "unknown")
y = y[(y.edu != "missing") & (y.gndr == 2)]
y["regime"] = y.cntry.map({c: r for r, cs in REGIMES.items() for c in cs})
w = y[y.regime.notna()].copy()
w["w"] = w.anweight * len(w) / w.anweight.sum()

F = ("neet ~ child + partner + age_c + I(age_c**2) + C(edu, Treatment('high'))"
     " + C(par_edu) + abroad + C(cntry)")


def gap(g):
    m = smf.glm(F, g, family=sm.families.Binomial(), var_weights=g.w).fit()
    p0 = np.average(m.predict(g.assign(child=0)), weights=g.w)
    p1 = np.average(m.predict(g.assign(child=1)), weights=g.w)
    return p0, p1


rng = np.random.default_rng(1)
rows = []
for regime, g in w.groupby("regime"):
    p0, p1 = gap(g)
    boots = []
    for _ in range(300):
        s = g.sample(len(g), replace=True, random_state=int(rng.integers(1e9)))
        try:
            b0, b1 = gap(s)
            boots.append(b1 - b0)
        except Exception:
            pass
    lo, hi = np.percentile(boots, [2.5, 97.5])
    rows.append(dict(regime=regime, no_child=p0 * 100, mother=p1 * 100, gap=(p1 - p0) * 100,
                     gap_lo=lo * 100, gap_hi=hi * 100,
                     n_women=len(g), n_mothers=int(g.child.sum())))
res = pd.DataFrame(rows).set_index("regime").sort_values("gap")

# Do regimes differ? Likelihood-ratio test of child x regime interaction (pooled)
full = smf.glm(F.replace("child +", "child * C(regime) +"), w, family=sm.families.Binomial(), var_weights=w.w).fit()
red = smf.glm(F.replace("child +", "child + C(regime) +"), w, family=sm.families.Binomial(), var_weights=w.w).fit()
lr = 2 * (full.llf - red.llf)
p_lr = stats.chi2.sf(lr, len(REGIMES) - 1)

(RES / "results.md").write_text(
    "# Results: motherhood gap in NEET by welfare regime (women 15-29)\n\n"
    + res.round(1).to_markdown()
    + f"\n\nTest of differences between regimes (LR, child × regime): χ² = {lr:.2f}, df = {len(REGIMES)-1}, p = {p_lr:.3f}.\n"
    "The gap is large and positive in every regime; differences between regimes are not statistically significant at 5%.\n")
print(res.round(1)); print(f"LR p = {p_lr:.3f}")

# ---------------------------------------------------------------- figure
S, T1, T2, T3 = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
BLUE, ORANGE, GRID = "#2a78d6", "#eb6834", "#e6e5e0"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": T1})
fig = plt.figure(figsize=(10, 12.5), dpi=130, facecolor=S)
fig.text(0.06, 0.955, "YOUTH NEET IN EUROPE · WELFARE SYSTEMS", fontsize=11.5, color=ORANGE, weight="bold")
fig.text(0.06, 0.935, "The motherhood gap shows up\nin every welfare system", fontsize=24, weight="bold", va="top", linespacing=1.15)
fig.text(0.06, 0.845, "Predicted probability of being NEET, women aged 15–29", fontsize=12, color=T2)

ax = fig.add_axes([0.30, 0.30, 0.64, 0.50], facecolor=S)
order = list(res.index)
for i, r in enumerate(order):
    v = res.loc[r]
    ax.plot([v.no_child, v.mother], [i, i], color=ORANGE, lw=7, alpha=0.3, solid_capstyle="round", zorder=1)
    ax.scatter([v.no_child], [i], s=200, color=BLUE, edgecolor=S, lw=2, zorder=2)
    ax.scatter([v.mother], [i], s=280, color=ORANGE, edgecolor=S, lw=2, zorder=3)
    ax.text(v.no_child - 1.5, i, f"{v.no_child:.0f}%", ha="right", va="center", fontsize=12, color=T2)
    ax.text(v.mother + 2, i, f"{v.mother:.0f}%", va="center", fontsize=14, weight="bold")
    ax.text(v.mother + 9.5, i, f"+{v.gap:.0f} pts", va="center", fontsize=11.5, color=ORANGE, weight="bold")
ax.set_yticks(range(len(order)))
ax.set_yticklabels([f"{r}\n" + f"{', '.join(REGIMES[r][:4])}{'…' if len(REGIMES[r]) > 4 else ''}" for r in order],
                   fontsize=12, color=T1, linespacing=1.4)
for lab in ax.get_yticklabels():
    lab.set_fontsize(12)
ax.set_xlim(0, 75); ax.set_xticks([0, 20, 40, 60]); ax.set_xticklabels(["0%", "20%", "40%", "60%"], color=T2)
ax.set_ylim(-0.7, len(order) - 0.4)
ax.grid(axis="x", color=GRID); ax.set_axisbelow(True); ax.tick_params(length=0)
for s in ax.spines.values(): s.set_visible(False)
ax.scatter([], [], s=90, color=BLUE, label="no child at home")
ax.scatter([], [], s=90, color=ORANGE, label="young mothers")
ax.legend(loc="upper center", bbox_to_anchor=(0.4, 1.08), ncol=2, frameon=False, fontsize=11.5)

nord = res.loc["Nordic"]
fig.text(0.06, 0.215, "Even in the Nordic countries,", fontsize=15, weight="bold")
fig.text(0.06, 0.185, f"young mothers are about {nord.mother / nord.no_child:.0f}× as likely to be NEET as other young women.",
         fontsize=13.5, color=T1)
fig.text(0.06, 0.03,
         f"Weighted logistic regression per regime; controls: partner, age, education, parental education, born abroad, country FE.\n"
         f"Differences between regimes are not statistically significant (p = {p_lr:.2f}).\n"
         "Young mothers in sample: " + ", ".join(f"{r.split()[0]} {int(res.loc[r].n_mothers)}" for r in order) + ".\n"
         "Source: European Social Survey Round 11 (2023–24).  Analysis: Tuğba G. · github.com/tugbasahingunes/neet-europe-analysis",
         fontsize=8.6, color=T2, linespacing=1.6)
fig.savefig(FIG / "neet_motherhood_by_regime.png", facecolor=S)
print("Done.")
