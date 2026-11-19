"""
Predicting youth NEET with machine learning: accuracy, explainability and fairness.

Data: ESS Round 11, ages 15-29 (sample as in analysis 02 plus background variables).
Models: (1) logistic regression, (2) LightGBM gradient boosting. Same features, survey weights.
Evaluation: 5-fold stratified cross-validation repeated 3 times: ROC AUC, average precision, Brier score.
Explainability: SHAP values (TreeExplainer) on out-of-fold predictions.
Fairness: performance and error rates by sex and by country group when the top 20% risk scores are flagged.

Run:  python analysis.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb
import shap
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
LABELS = {"age": "Age", "female": "Female", "own_education": "Own education", "parental_education": "Parental education",
          "child_at_home": "Child at home", "partner_at_home": "Partner at home", "household_size": "Household size",
          "born_abroad": "Born abroad", "parent_born_abroad": "Parent born abroad", "rurality": "Urban → rural residence",
          "father_not_working_at_14": "Father not working when 14", "mother_not_working_at_14": "Mother not working when 14",
          "country": "Country"}
FIG, RES = HERE / "figures", HERE / "results"
ess = pd.read_csv(HERE.parent / "02_ess_microdata" / "data" / "ESS11e04_2.csv", low_memory=False)

# ---------------------------------------------------------------- data
y = ess[ess.agea.between(15, 29) & ess.mnactic.isin([1, 2, 3, 4, 5, 7, 8, 9]) & ess.eisced.isin(range(1, 8))].copy()
y["neet"] = y.mnactic.isin([3, 4, 5, 8, 9]).astype(int)
grid = [c for c in ess.columns if c.startswith("rshipa")]


def valid(s, lo, hi):
    return s.where(s.between(lo, hi))


F = pd.DataFrame(index=y.index)
F["age"] = y.agea
F["female"] = (y.gndr == 2).astype(int)
F["own_education"] = y.eisced
F["parental_education"] = y[["eiscedf", "eiscedm"]].where(y[["eiscedf", "eiscedm"]].isin(range(1, 8))).max(axis=1)
F["child_at_home"] = (y[grid] == 2).any(axis=1).astype(int)
F["partner_at_home"] = (y[grid] == 1).any(axis=1).astype(int)
F["household_size"] = valid(y.hhmmb, 1, 20)
F["born_abroad"] = (y.brncntr == 2).astype(int)
F["parent_born_abroad"] = ((y.facntr == 2) | (y.mocntr == 2)).astype(int)
F["rurality"] = valid(y.domicil, 1, 5)
F["father_not_working_at_14"] = y.emprf14.map({1: 0, 2: 0, 3: 1, 4: 1})
F["mother_not_working_at_14"] = y.emprm14.map({1: 0, 2: 0, 3: 1, 4: 1})
F["country"] = y.cntry.astype("category")
target = y.neet.values
wts = (y.anweight * len(y) / y.anweight.sum()).values
sex = F.female.values
REGION = {**{c: "Nordic" for c in ["SE", "NO", "FI", "IS"]},
          **{c: "Continental" for c in ["AT", "BE", "CH", "DE", "FR", "NL"]},
          **{c: "Liberal" for c in ["GB", "IE"]},
          **{c: "Southern" for c in ["ES", "IT", "PT", "GR", "CY"]},
          **{c: "Central & Eastern" for c in ["BG", "HR", "EE", "HU", "LT", "LV", "PL", "SI", "SK"]}}
region = y.cntry.map(REGION).fillna("Other").values
print(f"n = {len(F)}, NEET = {target.sum()}")


def logit_matrix(df):
    X = df.drop(columns="country").copy()
    for c in X.columns:
        if X[c].isna().any():
            X[c + "_missing"] = X[c].isna().astype(int)
            X[c] = X[c].fillna(X[c].median())
    X["age_sq"] = (X.age - 22) ** 2
    X = pd.concat([X, pd.get_dummies(df.country, prefix="cty", drop_first=True).astype(int)], axis=1)
    return X


XL = logit_matrix(F)
params = dict(objective="binary", learning_rate=0.03, n_estimators=600, num_leaves=15, min_child_samples=40,
              subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, random_state=1)

# ---------------------------------------------------------------- cross-validation
cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=42)
oof = {"logit": np.zeros((3, len(F))), "lgbm": np.zeros((3, len(F)))}
for k, (tr, te) in enumerate(cv.split(F, target)):
    rep = k // 5
    sc = StandardScaler().fit(XL.iloc[tr])
    lr = LogisticRegression(max_iter=4000, C=1.0).fit(sc.transform(XL.iloc[tr]), target[tr], sample_weight=wts[tr])
    oof["logit"][rep, te] = lr.predict_proba(sc.transform(XL.iloc[te]))[:, 1]
    gb = lgb.LGBMClassifier(**params).fit(F.iloc[tr], target[tr], sample_weight=wts[tr], categorical_feature=["country"])
    oof["lgbm"][rep, te] = gb.predict_proba(F.iloc[te])[:, 1]


def metrics(p, mask=None):
    m = np.ones(len(p), bool) if mask is None else mask
    return dict(AUC=roc_auc_score(target[m], p[m], sample_weight=wts[m]),
                AP=average_precision_score(target[m], p[m], sample_weight=wts[m]),
                Brier=brier_score_loss(target[m], p[m], sample_weight=wts[m]))


perf = {}
for name in oof:
    reps = [metrics(oof[name][r]) for r in range(3)]
    perf[name] = {k: (np.mean([d[k] for d in reps]), np.std([d[k] for d in reps])) for k in reps[0]}
perf_tab = pd.DataFrame({n: {f"{k} (mean)": v[0] for k, v in d.items()} | {f"{k} (sd over repeats)": v[1] for k, v in d.items()}
                         for n, d in perf.items()}).T
base_rate = np.average(target, weights=wts)
print(perf_tab.round(3))

# ---------------------------------------------------------------- fairness at top-20% flagging
p_gb = oof["lgbm"].mean(axis=0)
thr = np.quantile(p_gb, 0.80)
flag = p_gb >= thr


def group_stats(mask):
    t, f, ww = target[mask], flag[mask], wts[mask]
    tpr = np.average(f[t == 1], weights=ww[t == 1]) if (t == 1).any() else np.nan
    fpr = np.average(f[t == 0], weights=ww[t == 0]) if (t == 0).any() else np.nan
    return dict(n=int(mask.sum()), NEET_rate=np.average(t, weights=ww), flagged=np.average(f, weights=ww),
                recall=tpr, false_positive_rate=fpr, AUC=roc_auc_score(t, p_gb[mask], sample_weight=ww))


fair = {"All": group_stats(np.ones(len(F), bool)), "Women": group_stats(sex == 1), "Men": group_stats(sex == 0)}
for r in ["Nordic", "Continental", "Liberal", "Southern", "Central & Eastern", "Other"]:
    fair[r] = group_stats(region == r)
fair_tab = pd.DataFrame(fair).T

# ---------------------------------------------------------------- SHAP (model fit on all data)
gb_full = lgb.LGBMClassifier(**params).fit(F, target, sample_weight=wts, categorical_feature=["country"])
explainer = shap.TreeExplainer(gb_full)
sv = explainer.shap_values(F)
sv = sv[1] if isinstance(sv, list) else sv
imp = pd.Series(np.abs(sv).mean(axis=0), index=F.columns).sort_values(ascending=False)
# interaction: child effect by sex
child_shap = pd.DataFrame({"female": sex, "child": F["child_at_home"].values, "shap_child": sv[:, list(F.columns).index("child_at_home")]})
child_eff = child_shap[child_shap.child == 1].groupby("female").shap_child.mean()

(RES / "results.md").write_text(
    "# Results: machine learning for youth NEET (ESS Round 11, ages 15-29)\n\n"
    f"n = {len(F):,}; weighted NEET rate {base_rate:.1%}. 5-fold stratified CV x 3 repeats, survey weights.\n\n"
    "## Predictive performance (out-of-fold)\n\n" + perf_tab.round(3).to_markdown()
    + f"\n\nAverage precision of a random model = base rate = {base_rate:.3f}.\n\n"
    "## Global feature importance (mean |SHAP|, log-odds scale)\n\n" + imp.round(3).to_frame("mean_abs_shap").to_markdown()
    + "\n\n## SHAP contribution of 'child at home' among those living with a child (log-odds)\n\n"
    + child_eff.rename({0: "men", 1: "women"}).round(3).to_frame("mean_shap").to_markdown()
    + f"\n\n## Fairness: flagging the top 20% of risk scores (threshold {thr:.3f})\n\n"
    "recall = share of NEET young people who are flagged; false_positive_rate = share of non-NEET who are flagged.\n\n"
    + fair_tab.round(3).to_markdown())
print(imp.round(3)); print(child_eff.round(3)); print(fair_tab.round(3))
np.save(RES / "_oof_lgbm.npy", p_gb)
pd.to_pickle(dict(perf=perf, imp=imp, fair=fair_tab, child=child_eff, base=base_rate, sv=sv, F=F, sex=sex), RES / "_cache.pkl")

# ---------------------------------------------------------------- figure
S, T1, T2, T3 = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
BLUE, ORANGE, GREY, GRID, LIGHT = "#2a78d6", "#eb6834", "#b5b4ad", "#e6e5e0", "#f2f1ed"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": T1})
fig = plt.figure(figsize=(10, 13.5), dpi=130, facecolor=S)
rec_m, rec_f = fair_tab.loc["Men", "recall"], fair_tab.loc["Women", "recall"]
fig.text(0.06, 0.962, "MACHINE LEARNING · EXPLAINABILITY · FAIRNESS", fontsize=11.5, color=ORANGE, weight="bold")
fig.text(0.06, 0.945, f"An AI early-warning tool for youth NEET\nwould miss {round((1-rec_m)*10)} in 10 young men who need support",
         fontsize=21, weight="bold", va="top", linespacing=1.18)
fig.text(0.06, 0.873, f"Predicting NEET status for {len(F):,} young Europeans (15–29) from background characteristics",
         fontsize=11.5, color=T2)

# panel 1: model comparison
fig.text(0.06, 0.835, "1  A complex model does not beat a simple one", fontsize=14.5, weight="bold")
ax1 = fig.add_axes([0.08, 0.685, 0.40, 0.125], facecolor=S)
mods = [("Logistic\nregression", "logit", GREY), ("Gradient\nboosting", "lgbm", BLUE)]
for i, (lab, k, col) in enumerate(mods):
    v = perf[k]["AUC"][0]
    ax1.bar(i, v, width=0.55, color=col); ax1.text(i, v + 0.008, f"{v:.2f}", ha="center", fontsize=14, weight="bold")
ax1.set_ylim(0.5, 0.8); ax1.set_xticks([0, 1]); ax1.set_xticklabels([m[0] for m in mods], fontsize=11)
ax1.set_yticks([]); ax1.tick_params(length=0); ax1.set_title("AUC (0.5 = coin flip)", fontsize=10.5, color=T2, loc="left")
for s in ax1.spines.values(): s.set_visible(False)
ax1.axhline(0.5, color=GREY, lw=1)
fig.text(0.53, 0.79, "Out-of-fold results, 5-fold cross-validation\nrepeated 3 times, survey-weighted.\n\n"
         f"Both models rank cases similarly well\n(AUC ≈ {perf['logit']['AUC'][0]:.2f}). The simpler, transparent\n"
         "model is just as good here.", fontsize=11, color=T1, va="top", linespacing=1.45)

# panel 2: SHAP
fig.text(0.06, 0.612, "2  What drives the predictions (SHAP)", fontsize=14.5, weight="bold")
ax2 = fig.add_axes([0.36, 0.43, 0.58, 0.17], facecolor=S)
top = imp.head(8)[::-1]
for i, (k, v) in enumerate(top.items()):
    ax2.barh(i, v, height=0.62, color=ORANGE if k in ("child_at_home", "female") else BLUE)
    ax2.text(v + 0.01, i, f"{v:.2f}", va="center", fontsize=10)
ax2.set_yticks(range(len(top))); ax2.set_yticklabels([LABELS[k] for k in top.index], fontsize=11)
ax2.set_xticks([]); ax2.tick_params(length=0)
for s in ax2.spines.values(): s.set_visible(False)
fig.text(0.06, 0.41, f"Mean absolute SHAP value (log-odds). Among those living with a child, the child raises predicted\n"
         f"risk almost twice as much for young women ({child_eff[1]:.2f}) as for young men ({child_eff[0]:.2f}).",
         fontsize=10, color=T2, va="top", linespacing=1.45)

# panel 3: fairness
fig.text(0.06, 0.355, "3  But it works very unequally", fontsize=14.5, weight="bold")
fig.text(0.06, 0.333, "Share of NEET young people who would be flagged if the top 20% of risk scores were contacted",
         fontsize=10.5, color=T2)
ax3 = fig.add_axes([0.30, 0.115, 0.62, 0.205], facecolor=S)
groups = ["Women", "Men", "Central & Eastern", "Southern", "Continental", "Liberal", "Nordic"]
for i, g in enumerate(groups[::-1]):
    v = fair_tab.loc[g, "recall"] * 100
    col = ORANGE if g == "Women" else (BLUE if g == "Men" else GREY)
    ax3.plot([0, v], [i, i], color=LIGHT, lw=9, solid_capstyle="round", zorder=1)
    ax3.scatter([v], [i], s=150, color=col, zorder=2)
    ax3.text(v + 3, i, f"{v:.0f}%", va="center", fontsize=12, weight="bold" if g in ("Women", "Men") else "normal")
ax3.axhline(len(groups) - 2.5, color=GRID, lw=1)
ax3.set_yticks(range(len(groups))); ax3.set_yticklabels(groups[::-1], fontsize=11.5)
ax3.set_xlim(0, 75); ax3.set_xticks([0, 25, 50, 75]); ax3.set_xticklabels(["0%", "25%", "50%", "75%"], color=T2)
ax3.tick_params(length=0); ax3.grid(axis="x", color=GRID); ax3.set_axisbelow(True)
for s in ax3.spines.values(): s.set_visible(False)

fig.text(0.06, 0.085, "Before using AI to target social support, test who it misses, not only how accurate it is.",
         fontsize=12.5, weight="bold")
fig.text(0.06, 0.02,
         "Features: age, sex, own and parental education, child/partner at home, household size, migration background, rurality,\n"
         "parents' employment at age 14, country. LightGBM with survey weights; SHAP TreeExplainer. Regions with < 1,000 cases are indicative.\n"
         "Source: European Social Survey Round 11 (2023–24).  Analysis: Tuğba G. · github.com/tugbasahingunes/neet-europe-analysis",
         fontsize=8.3, color=T2, linespacing=1.6)
fig.savefig(FIG / "ml_neet_fairness.png", facecolor=S)
print("Done.")
