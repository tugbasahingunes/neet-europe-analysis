"""
How much of the gender gap in youth NEET can be explained? An Oaxaca-Blinder decomposition.

Data: ESS Round 11, young people aged 15-29 (same sample as analysis 02).
Method: two-fold Oaxaca-Blinder decomposition of the women-men gap in NEET probability,
using a weighted linear probability model with pooled (Neumark) reference coefficients
that include a sex dummy (Jann 2008). Detailed contributions by variable group.
95% intervals from a cluster bootstrap over countries (500 replications).
Robustness: the same decomposition with men's and with women's coefficients as reference.

Run:  python analysis.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
FIG, RES = HERE / "figures", HERE / "results"
ess = pd.read_csv(HERE.parent / "02_ess_microdata" / "data" / "ESS11e04_2.csv", low_memory=False)

# ---------------------------------------------------------------- sample (as in 02)
y = ess[ess.agea.between(15, 29) & ess.mnactic.isin([1, 2, 3, 4, 5, 7, 8, 9])].copy()
y["neet"] = y.mnactic.isin([3, 4, 5, 8, 9]).astype(float)
grid = [c for c in ess.columns if c.startswith("rshipa")]
y["child"] = (y[grid] == 2).any(axis=1).astype(float)
y["partner"] = (y[grid] == 1).any(axis=1).astype(float)
y["female"] = (y.gndr == 2).astype(float)
y["abroad"] = (y.brncntr == 2).astype(float)
y["age_c"] = y.agea - 22.0
y["age_c2"] = y.age_c ** 2
y = y[y.eisced.isin(range(1, 8))]
y["edu_low"] = y.eisced.isin([1, 2]).astype(float)
y["edu_mid"] = y.eisced.isin([3, 4, 5]).astype(float)
par = y[["eiscedf", "eiscedm"]].where(y[["eiscedf", "eiscedm"]].isin(range(1, 8))).max(axis=1)
y["par_low"] = par.isin([1, 2]).astype(float)
y["par_mid"] = par.isin([3, 4, 5]).astype(float)
y["par_unknown"] = par.isna().astype(float)
y["w"] = y.anweight * len(y) / y.anweight.sum()
countries = sorted(y.cntry.unique())
for c in countries[1:]:
    y[f"c_{c}"] = (y.cntry == c).astype(float)

GROUPS = {
    "Child at home": ["child"],
    "Partner at home": ["partner"],
    "Own education": ["edu_low", "edu_mid"],
    "Age": ["age_c", "age_c2"],
    "Parental education": ["par_low", "par_mid", "par_unknown"],
    "Born abroad": ["abroad"],
    "Country": [f"c_{c}" for c in countries[1:]],
}
X = [v for vs in GROUPS.values() for v in vs]


def wls(Xm, yv, w):
    Xc = np.column_stack([np.ones(len(Xm)), Xm])
    sw = np.sqrt(w)
    beta, *_ = np.linalg.lstsq(Xc * sw[:, None], yv * sw, rcond=None)
    return beta


def decompose(d, reference="pooled"):
    f, m = d[d.female == 1], d[d.female == 0]
    xf = np.average(f[X], axis=0, weights=f.w); xm = np.average(m[X], axis=0, weights=m.w)
    yf = np.average(f.neet, weights=f.w); ym = np.average(m.neet, weights=m.w)
    if reference == "pooled":           # Neumark/Jann: pooled model incl. group dummy
        b = wls(np.column_stack([d[X].values, d.female.values]), d.neet.values, d.w.values)[1:-1]
    elif reference == "men":
        b = wls(m[X].values, m.neet.values, m.w.values)[1:]
    else:
        b = wls(f[X].values, f.neet.values, f.w.values)[1:]
    ic = X.index("child") + 1
    b_f_child = wls(f[X].values, f.neet.values, f.w.values)[ic]
    b_m_child = wls(m[X].values, m.neet.values, m.w.values)[ic]
    contrib = (xf - xm) * b
    detail = {g: contrib[[X.index(v) for v in vs]].sum() for g, vs in GROUPS.items()}
    explained = contrib.sum()
    return {"gap": yf - ym, "women": yf, "men": ym, "explained": explained,
            "unexplained": (yf - ym) - explained, "child_effect_women": b_f_child,
            "child_effect_men": b_m_child, "child_share_women": xf[X.index("child")],
            "child_share_men": xm[X.index("child")], **detail}


main = decompose(y)
rob = {r: decompose(y, r) for r in ("men", "women")}

# cluster bootstrap over countries
rng = np.random.default_rng(11)
boots = []
groups = {c: g for c, g in y.groupby("cntry")}
for _ in range(500):
    pick = rng.choice(countries, size=len(countries), replace=True)
    parts = []
    for i, c in enumerate(pick):
        g = groups[c].copy()
        parts.append(g)
    b = pd.concat(parts, ignore_index=True)
    # country dummies keep original codes; duplicated countries share a dummy (standard cluster bootstrap)
    try:
        boots.append(decompose(b))
    except np.linalg.LinAlgError:
        pass
B = pd.DataFrame(boots)
ci = B.quantile([0.025, 0.975]).T

rows = ["gap", "explained", "unexplained"] + list(GROUPS)
eff = pd.DataFrame({"estimate": [main[k] * 100 for k in ("child_effect_women", "child_effect_men", "child_share_women", "child_share_men")],
                    "ci_low": [ci.loc[k, 0.025] * 100 for k in ("child_effect_women", "child_effect_men", "child_share_women", "child_share_men")],
                    "ci_high": [ci.loc[k, 0.975] * 100 for k in ("child_effect_women", "child_effect_men", "child_share_women", "child_share_men")]},
                   index=["Effect of child at home on NEET, women (pts)", "Effect of child at home on NEET, men (pts)",
                          "Share living with a child, women (%)", "Share living with a child, men (%)"])
table = pd.DataFrame({"estimate_pts": [main[r] * 100 for r in rows],
                      "ci_low": [ci.loc[r, 0.025] * 100 for r in rows],
                      "ci_high": [ci.loc[r, 0.975] * 100 for r in rows],
                      "share_of_gap_%": [main[r] / main["gap"] * 100 for r in rows]}, index=rows)
robt = pd.DataFrame({k: {r: v[r] * 100 for r in rows} for k, v in
                     {"pooled (main)": main, "men's coefficients": rob["men"], "women's coefficients": rob["women"]}.items()})
(RES / "results.md").write_text(
    "# Results: Oaxaca-Blinder decomposition of the gender gap in youth NEET\n\n"
    f"Sample: {len(y):,} respondents aged 15-29, {len(countries)} countries (ESS Round 11). "
    f"Weighted NEET rate: women {main['women']*100:.1f}%, men {main['men']*100:.1f}%.\n\n"
    "Positive contributions widen the gap (women more likely NEET); negative ones narrow it.\n\n"
    "## Main decomposition (pooled reference, 95% cluster-bootstrap CI over countries, "
    f"{len(B)} replications)\n\n" + table.round(2).to_markdown()
    + "\n\n## Robustness: choice of reference coefficients (percentage points)\n\n" + robt.round(2).to_markdown()
    + "\n\n## Same characteristic, different consequence: child at home\n\n"
    "Coefficients from separate weighted linear probability models for women and men (same controls).\n\n"
    + eff.round(1).to_markdown())
print(table.round(2)); print(robt.round(2))

# ---------------------------------------------------------------- figure
S, T1, T2, T3 = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
BLUE, ORANGE, GREY, GRID, LIGHT = "#2a78d6", "#eb6834", "#b5b4ad", "#e6e5e0", "#f2f1ed"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": T1})
fig = plt.figure(figsize=(10, 12.5), dpi=130, facecolor=S)
fig.text(0.06, 0.957, "YOUTH NEET IN EUROPE · DECOMPOSITION ANALYSIS", fontsize=11.5, color=ORANGE, weight="bold")
fig.text(0.06, 0.937, "Same situation, different consequences:\nwhy young women are more often NEET",
         fontsize=22, weight="bold", va="top", linespacing=1.18)
fig.text(0.06, 0.852, f"Ages 15–29: women {main['women']*100:.1f}% vs men {main['men']*100:.1f}% NEET, a gap of "
         f"{main['gap']*100:.1f} percentage points", fontsize=12, color=T2)

# panel 1: explained vs unexplained
fig.text(0.06, 0.805, "1  Differences in characteristics explain only a small part", fontsize=15, weight="bold")
ax = fig.add_axes([0.30, 0.565, 0.64, 0.215], facecolor=S)
items = [("Total gap", main["gap"], T1), ("Child at home", main["Child at home"], ORANGE),
         ("Age", main["Age"], ORANGE), ("Own education", main["Own education"], BLUE),
         ("Other factors", main["Partner at home"] + main["Parental education"] + main["Born abroad"] + main["Country"], GREY),
         ("Not explained by\ncharacteristics", main["unexplained"], "#5a5955")]
for i, (lab, v, col) in enumerate(items):
    yy = len(items) - 1 - i
    ax.barh(yy, v * 100, color=col, height=0.62)
    ax.text(v * 100 + (0.12 if v >= 0 else -0.12), yy, f"{v*100:+.1f}" if i else f"{v*100:.1f} pts",
            va="center", ha="left" if v >= 0 else "right", fontsize=11.5, weight="bold" if i in (0, 5) else "normal")
ax.set_yticks(range(len(items))); ax.set_yticklabels([it[0] for it in items][::-1], fontsize=11.5)
ax.axvline(0, color=GREY, lw=1); ax.set_xlim(-1.6, 7.2); ax.set_xticks([]); ax.tick_params(length=0)
for s in ax.spines.values(): s.set_visible(False)
fig.text(0.06, 0.535, f"Young women are better educated than young men, which narrows the gap ({main['Own education']*100:+.1f} pts).\n"
         f"More of them live with a child, which widens it ({main['Child at home']*100:+.1f} pts). But {main['unexplained']/main['gap']*100:.0f}% of the gap\n"
         "remains after accounting for who young women and men are.", fontsize=11, color=T2, linespacing=1.5, va="top")

# panel 2: different consequences of a child at home
fig.text(0.06, 0.43, "2  The same situation has very different consequences", fontsize=15, weight="bold")
fig.text(0.06, 0.405, "Change in the probability of being NEET when a young person lives with a child (same controls)",
         fontsize=11, color=T2)
ax2 = fig.add_axes([0.30, 0.20, 0.64, 0.18], facecolor=S)
for i, (lab, k, col) in enumerate((("Young women", "women", ORANGE), ("Young men", "men", BLUE))):
    v = main[f"child_effect_{k}"] * 100
    lo, hi = ci.loc[f"child_effect_{k}", 0.025] * 100, ci.loc[f"child_effect_{k}", 0.975] * 100
    yy = 1 - i
    ax2.barh(yy, v, color=col, height=0.55)
    ax2.plot([lo, hi], [yy, yy], color=T1, lw=1.4); ax2.plot([lo, lo], [yy - .1, yy + .1], color=T1, lw=1.4); ax2.plot([hi, hi], [yy - .1, yy + .1], color=T1, lw=1.4)
    ax2.text(max(hi, v) + 1.2, yy, f"+{v:.0f} pts", va="center", fontsize=17, weight="bold")
ax2.set_yticks([1, 0]); ax2.set_yticklabels(["Young women", "Young men"], fontsize=12.5)
ax2.set_xlim(-4, 62); ax2.set_xticks([]); ax2.tick_params(length=0); ax2.axvline(0, color=GREY, lw=1)
for s in ax2.spines.values(): s.set_visible(False)
fig.text(0.06, 0.165, "Black lines: 95% confidence intervals.", fontsize=9.5, color=T3)
fig.text(0.06, 0.125, "The gap is not about young women themselves. It reflects how well young\nparents, especially mothers, are supported to combine family, education and work.",
         fontsize=13, weight="bold", linespacing=1.4, va="center")
fig.text(0.06, 0.03,
         f"Two-fold Oaxaca–Blinder decomposition, weighted linear probability model, pooled reference coefficients (Neumark/Jann);\n"
         f"robust in direction to men's or women's coefficients as reference. n = {len(y):,}, ages 15–29, 30 countries, country fixed effects;\n"
         f"95% CIs from a {len(B)}-replication cluster bootstrap over countries. Source: European Social Survey Round 11 (2023–24).\n"
         "Analysis: Tuğba G. · github.com/tugbasahingunes/neet-europe-analysis",
         fontsize=8.4, color=T2, linespacing=1.6)
fig.savefig(FIG / "gender_gap_decomposition.png", facecolor=S)
print("Done.")
