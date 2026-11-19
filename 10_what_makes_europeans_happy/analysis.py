"""
What makes Europeans happy? Four methods, one question.

Data: European Social Survey Round 11 (2023-24), adults aged 18+, 30 countries.
Outcome: "Taking all things together, how happy would you say you are?" (0-10).

Methods
  1. Multiple imputation (5 data sets, chained equations) for missing household income decile.
  2. OLS with country fixed effects, pooled with Rubin's rules.
  3. Dominance analysis (Shapley decomposition of R²) for 8 groups of predictors.
  4. Natural cubic splines for age and income (non-linear partial effects).
  5. Gradient boosting (LightGBM) + SHAP, 5-fold cross-validated R².
  6. Multilevel (random-intercept) model: share of variance between countries, and how much
     of it individual characteristics explain.

Run:  python analysis.py
"""
from pathlib import Path
from itertools import combinations
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.linear_model import BayesianRidge
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score
import lightgbm as lgb
import shap

HERE = Path(__file__).parent
FIG, RES = HERE / "figures", HERE / "results"
ess = pd.read_csv(HERE.parent / "02_ess_microdata" / "data" / "ESS11e04_2.csv", low_memory=False)


def v(s, lo, hi):
    return s.where(s.between(lo, hi))


d = ess[ess.agea.between(18, 100)].copy()
D = pd.DataFrame({
    "happy": v(d.happy, 0, 10),
    "age": d.agea.astype(float),
    "female": (d.gndr == 2).astype(float),
    "education": v(d.eisced, 1, 7),
    "income_decile": v(d.hinctnta, 1, 10),
    "income_feeling": 5 - v(d.hincfel, 1, 4),            # 4 = living comfortably
    "health": 6 - v(d.health, 1, 5),                       # 5 = very good
    "hampered": v(d.hlthhmp, 1, 3).map({1: 2, 2: 1, 3: 0}),  # 2 = hampered a lot
    "meet_friends": v(d.sclmeet, 1, 7),                    # 7 = every day
    "close_confidants": v(d.inprdsc, 0, 6),
    "social_activity": v(d.sclact, 1, 5),                  # 5 = much more than others
    "trust_people": v(d.ppltrst, 0, 10),
    "feel_safe": 5 - v(d.aesfdrk, 1, 4),                   # 4 = very safe
    "discriminated": (d.dscrgrp == 1).astype(float),
    "partner": (d[[c for c in d.columns if c.startswith("rshipa")]] == 1).any(axis=1).astype(float),
    "child_at_home": (d[[c for c in d.columns if c.startswith("rshipa")]] == 2).any(axis=1).astype(float),
    "unemployed": d.mnactic.isin([3, 4]).astype(float),
    "retired": (d.mnactic == 6).astype(float),
    "in_education": (d.mnactic == 2).astype(float),
    "rurality": v(d.domicil, 1, 5),
    "born_abroad": (d.brncntr == 2).astype(float),
    "country": d.cntry.values,
    "w": d.anweight.values,
})
D = D[D.happy.notna()]
core = [c for c in D.columns if c not in ("income_decile", "country", "w", "happy")]
D = D.dropna(subset=core).reset_index(drop=True)
D["w"] = D.w * len(D) / D.w.sum()
print(f"n = {len(D)}, income missing = {D.income_decile.isna().mean():.1%}")

GROUPS = {
    "Health": ["health", "hampered"],
    "Social relationships": ["meet_friends", "close_confidants", "social_activity", "partner"],
    "Money": ["income_decile", "income_feeling"],
    "Trust & safety": ["trust_people", "feel_safe", "discriminated"],
    "Work status": ["unemployed", "retired", "in_education"],
    "Demographics": ["age", "age2", "female", "born_abroad", "child_at_home", "rurality"],
    "Education": ["education"],
    "Country": ["country"],
}

# ---------------------------------------------------------------- 1. multiple imputation
M = 5
num = [c for c in D.columns if c not in ("country", "w")]
cdum = pd.get_dummies(D.country, prefix="c", drop_first=True).astype(float)
imputed = []
for m in range(M):
    imp = IterativeImputer(estimator=BayesianRidge(), sample_posterior=True, max_iter=10, random_state=m)
    Z = pd.DataFrame(imp.fit_transform(pd.concat([D[num], cdum], axis=1)), columns=num + list(cdum.columns))
    Dm = D.copy()
    Dm["income_decile"] = Z.income_decile.clip(1, 10).round()
    Dm["age2"] = (Dm.age - 50) ** 2 / 100
    imputed.append(Dm)

# ---------------------------------------------------------------- 2. OLS + Rubin's rules (standardised outcome & predictors)
preds = [x for g in GROUPS.values() for x in g if x != "country"]
fml = "happy ~ " + " + ".join(preds) + " + C(country)"
est, var = [], []
for Dm in imputed:
    Z = Dm.copy()
    for c in preds + ["happy"]:
        Z[c] = (Z[c] - np.average(Z[c], weights=Z.w)) / np.sqrt(np.cov(Z[c], aweights=Z.w))
    r = smf.wls(fml, Z, weights=Z.w).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(Z.country)[0]})
    est.append(r.params[preds]); var.append(r.bse[preds] ** 2)
est, var = pd.DataFrame(est), pd.DataFrame(var)
qbar = est.mean(); W_ = var.mean(); B_ = est.var(ddof=1); T = W_ + (1 + 1 / M) * B_
ols = pd.DataFrame({"beta_std": qbar, "se": np.sqrt(T)})
ols["ci_low"], ols["ci_high"] = ols.beta_std - 1.96 * ols.se, ols.beta_std + 1.96 * ols.se
ols = ols.sort_values("beta_std", key=abs, ascending=False)
print(ols.round(3).head(12))

# ---------------------------------------------------------------- 3. dominance analysis (Shapley R²), imputation 1
D1 = imputed[0]
y_ = D1.happy.values; w_ = D1.w.values
Xg = {g: (pd.get_dummies(D1.country, drop_first=True).astype(float).values if g == "Country" else D1[cols].values)
      for g, cols in GROUPS.items()}
names = list(GROUPS)
cache = {}


def r2(subset):
    key = frozenset(subset)
    if key in cache: return cache[key]
    if not subset: cache[key] = 0.0; return 0.0
    X = np.column_stack([np.ones(len(y_))] + [Xg[g] for g in subset]); sw = np.sqrt(w_)
    b = np.linalg.lstsq(X * sw[:, None], y_ * sw, rcond=None)[0]
    res = y_ - X @ b; ym = np.average(y_, weights=w_)
    cache[key] = 1 - np.sum(w_ * res ** 2) / np.sum(w_ * (y_ - ym) ** 2)
    return cache[key]


from math import factorial
n_g = len(names); shap_r2 = {}
for g in names:
    others = [o for o in names if o != g]; tot = 0.0
    for k in range(len(others) + 1):
        wk = factorial(k) * factorial(n_g - k - 1) / factorial(n_g)
        for S in combinations(others, k):
            tot += wk * (r2(list(S) + [g]) - r2(list(S)))
    shap_r2[g] = tot
dom = pd.Series(shap_r2).sort_values(ascending=False)
full_r2 = r2(names)
print("full R2", round(full_r2, 3)); print((dom / full_r2 * 100).round(1))

# ---------------------------------------------------------------- 4. splines (age, income), imputation 1
other = [p for p in preds if p not in ("age", "age2", "income_decile")]
fs = "happy ~ cr(age, df=5) + cr(income_decile, df=4) + " + " + ".join(other) + " + C(country)"
sp = smf.wls(fs, D1, weights=D1.w).fit()
grid_age = D1.iloc[[0] * 63].copy(); grid_age["age"] = np.arange(18, 81)
grid_inc = D1.iloc[[0] * 10].copy(); grid_inc["income_decile"] = np.arange(1, 11)


def partial(grid, var):
    base = D1.copy(); out = []
    for val in grid[var]:
        base[var] = val; out.append(np.average(sp.predict(base), weights=base.w))
    return np.array(out)


age_curve = partial(grid_age, "age"); inc_curve = partial(grid_inc, "income_decile")
age_raw = D1.groupby(D1.age.clip(18, 80).astype(int)).apply(lambda g: np.average(g.happy, weights=g.w))

# ---------------------------------------------------------------- 5. LightGBM + SHAP
F = D1[[p for p in preds if p != "age2"]].copy(); F["country"] = D1.country.astype("category")
prm = dict(objective="regression", learning_rate=0.03, n_estimators=700, num_leaves=31, min_child_samples=50,
           subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1, random_state=1)
oof = np.zeros(len(F)); oof_lin = np.zeros(len(F))
Xlin = pd.concat([D1[preds], pd.get_dummies(D1.country, drop_first=True).astype(float)], axis=1).values
for tr, te in KFold(5, shuffle=True, random_state=7).split(F):
    oof[te] = lgb.LGBMRegressor(**prm).fit(F.iloc[tr], y_[tr], sample_weight=w_[tr]).predict(F.iloc[te])
    X1 = np.column_stack([np.ones(len(tr)), Xlin[tr]]); sw = np.sqrt(w_[tr])
    b = np.linalg.lstsq(X1 * sw[:, None], y_[tr] * sw, rcond=None)[0]
    oof_lin[te] = np.column_stack([np.ones(len(te)), Xlin[te]]) @ b
cv = {"OLS": r2_score(y_, oof_lin, sample_weight=w_), "LightGBM": r2_score(y_, oof, sample_weight=w_)}
gbm = lgb.LGBMRegressor(**prm).fit(F, y_, sample_weight=w_)
sv = shap.TreeExplainer(gbm).shap_values(F)
shap_imp = pd.Series(np.abs(sv).mean(axis=0), index=F.columns).sort_values(ascending=False)
print(cv); print(shap_imp.round(3).head(10))

# ---------------------------------------------------------------- 6. multilevel variance decomposition
m0 = smf.mixedlm("happy ~ 1", D1, groups=D1.country).fit(reml=True)
icc0 = m0.cov_re.iloc[0, 0] / (m0.cov_re.iloc[0, 0] + m0.scale)
m1 = smf.mixedlm("happy ~ " + " + ".join(preds), D1, groups=D1.country).fit(reml=True)
between_expl = 1 - m1.cov_re.iloc[0, 0] / m0.cov_re.iloc[0, 0]
within_expl = 1 - m1.scale / m0.scale
print("ICC", round(icc0, 3), "between explained", round(between_expl, 3), "within explained", round(within_expl, 3))

# ---------------------------------------------------------------- save
pd.to_pickle(dict(ols=ols, dom=dom, full_r2=full_r2, age_curve=age_curve, inc_curve=inc_curve, age_raw=age_raw,
                  cv=cv, shap_imp=shap_imp, icc=icc0, between=between_expl, within=within_expl, n=len(D),
                  inc_missing=D.income_decile.isna().mean(), mean_happy=np.average(D.happy, weights=D.w)),
               RES / "_cache.pkl")
(RES / "results.md").write_text(
    "# Results: what makes Europeans happy? (ESS Round 11, adults 18+)\n\n"
    f"n = {len(D):,} in 30 countries; weighted mean happiness {np.average(D.happy, weights=D.w):.2f} (0-10). "
    f"Household income decile missing for {D.income_decile.isna().mean():.1%}; imputed with chained equations (m = {M}).\n\n"
    f"## Dominance analysis (Shapley decomposition of R², full R² = {full_r2:.3f})\n\n"
    + pd.DataFrame({"R2_share": dom, "percent_of_explained": dom / full_r2 * 100}).round(3).to_markdown()
    + "\n\n## OLS with country fixed effects, standardised coefficients, pooled over imputations (Rubin), SEs clustered by country\n\n"
    + ols.round(3).to_markdown()
    + f"\n\n## Cross-validated R² (5-fold)\n\n" + pd.Series(cv).round(3).to_frame("R2").to_markdown()
    + "\n\n## LightGBM mean |SHAP| (points on 0-10 scale)\n\n" + shap_imp.round(3).to_frame("mean_abs_shap").to_markdown()
    + f"\n\n## Multilevel model\n\nICC (share of variance between countries, empty model): {icc0:.3f}. "
      f"Individual characteristics explain {between_expl:.0%} of between-country variance and {within_expl:.0%} of within-country variance.\n"
    + "\n\n## Spline partial effects (predicted happiness, all else at observed values)\n\n"
    + pd.DataFrame({"age": np.arange(18, 81), "predicted": age_curve}).iloc[::5].round(2).to_markdown(index=False)
    + "\n\n" + pd.DataFrame({"income_decile": np.arange(1, 11), "predicted": inc_curve}).round(2).to_markdown(index=False))
print("saved")

# ---------------------------------------------------------------- figure
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
S, T1, T2, T3 = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
BLUE, ORANGE, GREY, GRID, LIGHT = "#2a78d6", "#eb6834", "#b5b4ad", "#e6e5e0", "#f2f1ed"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": T1})
fig = plt.figure(figsize=(10, 13.5), dpi=130, facecolor=S)
fig.text(0.06, 0.962, "WELLBEING IN EUROPE · 30 COUNTRIES · 46,000 ADULTS", fontsize=11.5, color=ORANGE, weight="bold")
fig.text(0.06, 0.945, "What makes Europeans happy?\nRelationships and health, more than money",
         fontsize=22, weight="bold", va="top", linespacing=1.18)
fig.text(0.06, 0.875, "European Social Survey 2023–24 · four methods, one question", fontsize=12, color=T2)

# panel 1: dominance
fig.text(0.06, 0.835, "1  Share of explained differences in happiness", fontsize=14.5, weight="bold")
fig.text(0.06, 0.814, "Dominance analysis (Shapley decomposition of R²)", fontsize=10.5, color=T2)
ax1 = fig.add_axes([0.32, 0.575, 0.62, 0.225], facecolor=S)
share = (dom / full_r2 * 100)[::-1]
for i, (g, s) in enumerate(share.items()):
    col = ORANGE if g in ("Social relationships", "Health") else (BLUE if g == "Money" else GREY)
    ax1.barh(i, s, height=0.64, color=col)
    ax1.text(s + 0.6, i, f"{s:.0f}%", va="center", fontsize=12, weight="bold" if col != GREY else "normal")
ax1.set_yticks(range(len(share))); ax1.set_yticklabels(share.index, fontsize=12)
ax1.set_xlim(0, 32); ax1.set_xticks([]); ax1.tick_params(length=0)
for s_ in ax1.spines.values(): s_.set_visible(False)

# panel 2a: money
fig.text(0.06, 0.53, "2  It's not how much you earn", fontsize=14.5, weight="bold")
fig.text(0.06, 0.509, "Effect on happiness (standardised, all else equal)", fontsize=10.5, color=T2)
ax2 = fig.add_axes([0.06, 0.345, 0.40, 0.15], facecolor=S)
mv = [("Feeling you can\nget by on income", "income_feeling", BLUE), ("Income level\n(decile)", "income_decile", GREY)]
for i, (lab, k, col) in enumerate(mv):
    b = ols.loc[k, "beta_std"]; lo, hi = ols.loc[k, "ci_low"], ols.loc[k, "ci_high"]
    ax2.bar(i, b, width=0.55, color=col)
    ax2.plot([i, i], [lo, hi], color=T1, lw=1.3)
    ax2.text(i, max(b, hi) + 0.012, f"{b:.2f}", ha="center", fontsize=14, weight="bold")
ax2.axhline(0, color=GREY, lw=1); ax2.set_ylim(-0.04, 0.24)
ax2.set_xticks([0, 1]); ax2.set_xticklabels([m[0] for m in mv], fontsize=10.5); ax2.set_yticks([]); ax2.tick_params(length=0)
for s_ in ax2.spines.values(): s_.set_visible(False)
fig.text(0.06, 0.288, "Once financial security is accounted for,\nthe income level itself adds almost nothing.",
         fontsize=10.5, color=T1, va="top", linespacing=1.4)

# panel 2b: age U
fig.text(0.53, 0.53, "3  Happiness dips around 40", fontsize=14.5, weight="bold")
fig.text(0.53, 0.509, "Predicted happiness by age, all else equal (splines)", fontsize=10.5, color=T2)
ax3 = fig.add_axes([0.56, 0.345, 0.38, 0.15], facecolor=S)
ages = np.arange(18, 81)
ax3.plot(ages, age_curve, color=ORANGE, lw=3)
amin = ages[np.argmin(age_curve)]
ax3.scatter([amin], [age_curve.min()], s=60, color=ORANGE, zorder=3)
ax3.text(amin, age_curve.min() - 0.03, f"lowest at {amin}\n({age_curve.min():.2f})", ha="center", va="top", fontsize=10.5)
ax3.text(18, age_curve[0] + 0.03, f"{age_curve[0]:.2f}", ha="left", fontsize=10, color=T2)
ax3.text(80, age_curve[-1] + 0.03, f"{age_curve[-1]:.2f}", ha="right", fontsize=10, color=T2)
ax3.set_ylim(age_curve.min() - 0.17, age_curve.max() + 0.1)
ax3.set_xticks([20, 40, 60, 80]); ax3.set_yticks([]); ax3.tick_params(length=0, labelsize=10.5)
ax3.grid(axis="x", color=GRID); ax3.set_axisbelow(True)
for s_ in ("top", "right", "left"): ax3.spines[s_].set_visible(False)
ax3.spines["bottom"].set_color(GRID)
fig.text(0.53, 0.288, "The classic U-shape appears once health,\nincome and relationships are held equal.",
         fontsize=10.5, color=T1, va="top", linespacing=1.4)

# panel 4: methods agree
fig.text(0.06, 0.235, "4  Robust across methods", fontsize=14.5, weight="bold")
boxes = [("Gradient boosting + SHAP", f"Same top drivers: health,\nfeeling secure, partner.\nCV R² {cv['LightGBM']:.2f} vs OLS {cv['OLS']:.2f}"),
         ("Multilevel model", f"{icc0:.0%} of differences lie\nbetween countries; individual\nfactors explain {between_expl:.0%} of them"),
         ("Multiple imputation", f"{D.income_decile.isna().mean():.0%} missing income imputed\n(5 data sets, Rubin's rules)")]
for i, (h, t) in enumerate(boxes):
    x = 0.06 + i * 0.30
    fig.patches.append(matplotlib.patches.FancyBboxPatch((x, 0.10), 0.28, 0.115, boxstyle="round,pad=0.004,rounding_size=0.012",
                                                         transform=fig.transFigure, facecolor=LIGHT, edgecolor="none"))
    fig.text(x + 0.015, 0.205, h, fontsize=11, weight="bold", va="top")
    fig.text(x + 0.015, 0.177, t, fontsize=9.6, color=T2, va="top", linespacing=1.4)
fig.text(0.06, 0.02,
         "Happiness: 0–10 scale. Adults 18+, n = 46,006, survey-weighted; country fixed effects; SEs clustered by country.\n"
         "Predictors: health, social contacts and confidants, partner, income decile and income feeling, trust, safety, discrimination,\n"
         "work status, age, sex, education, children at home, rurality, migration background. Source: European Social Survey Round 11.\n"
         "Analysis: Tuğba G. · github.com/tugbasahingunes/neet-europe-analysis",
         fontsize=8.2, color=T2, linespacing=1.6)
fig.savefig(FIG / "what_makes_europeans_happy.png", facecolor=S)
print("figure done")
