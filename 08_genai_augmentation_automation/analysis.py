"""
Will generative AI help or replace? Augmentation vs automation potential by gender.

Data
  - ILO occupational classification of GenAI potential (Gmyrek et al. 2023, ILO Working Paper 96),
    as included in the 2025 ILO-NASK release (column potential23): Augmentation potential,
    Automation potential, "Big unknown", Not affected. CC BY 4.0.
  - European Social Survey Round 11 (2023-24): employed respondents aged 18-66.

Methods
  1. Weighted shares by sex.
  2. Weighted logistic regressions for automation and augmentation potential with controls
     (age, education, industry, part-time, public sector, country), average predicted probabilities
     for women and men (cluster-robust SEs by country).
  3. Two-fold Oaxaca-Blinder decomposition (weighted LPM, pooled reference with sex dummy)
     of the gender gap in automation potential; cluster bootstrap over countries (300 reps).

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
FIG, RES = HERE / "figures", HERE / "results"
occ = pd.read_csv(HERE.parent / "05_genai_exposure_gender" / "data" / "ilo_genai_exposure_isco08_2025.csv")
if "potential23" not in occ.columns:
    raise SystemExit("Re-export the ILO table with potential23 (see 05/data).")
ess = pd.read_csv(HERE.parent / "02_ess_microdata" / "data" / "ESS11e04_2.csv", low_memory=False)

# ---------------------------------------------------------------- sample
w = ess[(ess.mnactic == 1) & ess.agea.between(18, 66) & (ess.isco08 < 10000)].copy()
n_all = len(w)
w = w.merge(occ[["ISCO_08", "potential23"]], left_on="isco08", right_on="ISCO_08", how="inner")  # 4-digit only
w["automation"] = (w.potential23 == "Automation Potential").astype(float)
w["augmentation"] = (w.potential23 == "Augmentation Potential").astype(float)
w["female"] = (w.gndr == 2).astype(float)
w["age_c"] = w.agea - 42.0
w["age_c2"] = w.age_c ** 2
w["edu"] = np.select([w.eisced.isin([1, 2]), w.eisced.isin([3, 4, 5]), w.eisced.isin([6, 7])], ["low", "mid", "high"], "")
# NACE Rev.2 2-digit -> broad industry groups
n = w.nacer2
w["industry"] = np.select(
    [n.between(1, 3), n.between(5, 43), n.between(45, 56), n.between(58, 66) | n.between(69, 75),
     n.between(77, 82) | n.between(68, 68), n.between(84, 84), n.between(85, 88), n.between(90, 99)],
    ["Agriculture", "Industry & construction", "Trade, transport & hospitality", "ICT, finance & professional",
     "Admin & real estate", "Public administration", "Education, health & social work", "Other services"], "")
w["part_time"] = (w.wkhtot < 30).astype(float)
w["public"] = w.tporgwk.isin([1, 2, 3]).astype(float)
w = w[(w.edu != "") & (w.industry != "") & (w.wkhtot < 666) & w.tporgwk.isin([1, 2, 3, 4, 5, 6])].copy()
w["w"] = w.anweight * len(w) / w.anweight.sum()
print(f"workers {n_all}, analytic sample {len(w)}")


def wshare(df, col):
    return np.average(df[col], weights=df.w) * 100


shares = pd.DataFrame({sx: {c: wshare(w[w.female == f], c) for c in ("augmentation", "automation")}
                       for sx, f in (("women", 1), ("men", 0))})

# ---------------------------------------------------------------- logistic models
F = ("{y} ~ female + age_c + age_c2 + C(edu, Treatment('high')) + C(industry) + part_time + public + C(cntry)")
logit = {}
for yv in ("automation", "augmentation"):
    m = smf.glm(F.format(y=yv), w, family=sm.families.Binomial(), var_weights=w.w).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(w.cntry)[0]})
    pf = np.average(m.predict(w.assign(female=1.0)), weights=w.w) * 100
    pm = np.average(m.predict(w.assign(female=0.0)), weights=w.w) * 100
    logit[yv] = dict(women=pf, men=pm, odds_ratio=np.exp(m.params["female"]),
                     or_low=np.exp(m.conf_int().loc["female", 0]), or_high=np.exp(m.conf_int().loc["female", 1]),
                     p=m.pvalues["female"])
logit = pd.DataFrame(logit).T

# ---------------------------------------------------------------- Oaxaca-Blinder for automation
dum = pd.get_dummies(w[["edu", "industry", "cntry"]], drop_first=False).astype(float)
edu_cols = ["edu_low", "edu_mid"]
ind_cols = [c for c in dum.columns if c.startswith("industry_") and c != "industry_ICT, finance & professional"]
cty_cols = [c for c in dum.columns if c.startswith("cntry_")][1:]
W = pd.concat([w.reset_index(drop=True), dum.reset_index(drop=True)], axis=1)
GROUPS = {"Industry": ind_cols, "Education": edu_cols, "Part-time work": ["part_time"],
          "Public sector": ["public"], "Age": ["age_c", "age_c2"], "Country": cty_cols}
X = [v for vs in GROUPS.values() for v in vs]


def wls(Xm, yv, wt):
    Xc = np.column_stack([np.ones(len(Xm)), Xm]); sw = np.sqrt(wt)
    return np.linalg.lstsq(Xc * sw[:, None], yv * sw, rcond=None)[0]


def decompose(d):
    f, m = d[d.female == 1], d[d.female == 0]
    xf = np.average(f[X], axis=0, weights=f.w); xm = np.average(m[X], axis=0, weights=m.w)
    yf = np.average(f.automation, weights=f.w); ym = np.average(m.automation, weights=m.w)
    b = wls(np.column_stack([d[X].values, d.female.values]), d.automation.values, d.w.values)[1:-1]
    c = (xf - xm) * b
    out = {"gap": yf - ym, "explained": c.sum(), "unexplained": (yf - ym) - c.sum()}
    out.update({g: c[[X.index(v) for v in vs]].sum() for g, vs in GROUPS.items()})
    return out


dec = decompose(W)
rng = np.random.default_rng(3)
cs = sorted(W.cntry.unique()); byc = {c: g for c, g in W.groupby("cntry")}
B = pd.DataFrame([decompose(pd.concat([byc[c] for c in rng.choice(cs, len(cs))], ignore_index=True)) for _ in range(300)])
ci = B.quantile([0.025, 0.975]).T
dect = pd.DataFrame({"pts": pd.Series(dec) * 100, "ci_low": ci[0.025] * 100, "ci_high": ci[0.975] * 100,
                     "share_%": pd.Series(dec) / dec["gap"] * 100})

(RES / "results.md").write_text(
    "# Results: augmentation vs automation potential by gender\n\n"
    f"Employed ESS respondents aged 18-66 with an occupation code: {n_all:,}; matched at 4 digits with complete covariates: {len(w):,}.\n\n"
    "## Weighted shares (%)\n\n" + shares.round(1).to_markdown()
    + "\n\n## Logistic regressions (controls: age, education, industry, part-time, public sector, country; SEs clustered by country)\n\n"
    + logit.round(3).to_markdown()
    + "\n\n## Oaxaca-Blinder decomposition of the automation-potential gap (women - men), percentage points\n\n"
    + dect.round(2).to_markdown())
print(shares.round(1)); print(logit.round(2)); print(dect.round(2))

# ---------------------------------------------------------------- figure
S, T1, T2, T3 = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
BLUE, ORANGE, GREY, GREEN = "#2a78d6", "#eb6834", "#b5b4ad", "#2a9d6f"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": T1})
fig = plt.figure(figsize=(10, 12.5), dpi=130, facecolor=S)
fig.text(0.06, 0.957, "GENERATIVE AI & WORK · 30 EUROPEAN COUNTRIES", fontsize=11.5, color=ORANGE, weight="bold")
fig.text(0.06, 0.937, "Generative AI can support the work of\nwomen and men in similar numbers. Where it\ncould take over tasks, women are more exposed",
         fontsize=21, weight="bold", va="top", linespacing=1.18)
fig.text(0.06, 0.822, "Share of workers by the kind of impact generative AI can have on their job", fontsize=12, color=T2)

# panel 1: grouped bars
ax = fig.add_axes([0.08, 0.53, 0.86, 0.26], facecolor=S)
cats = [("augmentation", "AI can support the work\n(augmentation potential)"), ("automation", "AI could take over many tasks\n(automation potential)")]
for i, (k, lab) in enumerate(cats):
    for j, (sx, col) in enumerate((("women", ORANGE), ("men", BLUE))):
        v = shares.loc[k, sx]; x = i * 1.2 + (j - 0.5) * 0.42
        ax.bar(x, v, width=0.38, color=col)
        ax.text(x, v + 0.4, f"{v:.1f}%", ha="center", fontsize=15, weight="bold")
ax.set_xticks([0, 1.2]); ax.set_xticklabels([c[1] for c in cats], fontsize=12)
ax.set_ylim(0, 20); ax.set_yticks([]); ax.tick_params(length=0)
for s in ax.spines.values(): s.set_visible(False)
ax.axhline(0, color=GREY, lw=1)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=ORANGE, label="women"), Patch(color=BLUE, label="men")], frameon=False, fontsize=11.5, loc="upper right", bbox_to_anchor=(1.0, 1.08))
ratio = shares.loc["automation", "women"] / shares.loc["automation", "men"]
ax.text(1.2, 11.5, f"{ratio:.1f}×", ha="center", fontsize=26, weight="bold", color=ORANGE)

# panel 2: same job context
la = logit.loc["automation"]
fig.text(0.06, 0.445, "Not just a matter of education or industry", fontsize=15, weight="bold")
fig.text(0.06, 0.42, "Automation potential, comparing women and men of the same age, education, industry,\n"
         "working hours, sector and country", fontsize=11, color=T2, va="top", linespacing=1.4)
fig.text(0.06, 0.33, f"{la.women:.1f}%", fontsize=30, weight="bold", color=ORANGE, va="center")
fig.text(0.06, 0.295, "women", fontsize=12, color=T2, va="center")
fig.text(0.30, 0.33, f"{la.men:.1f}%", fontsize=30, weight="bold", color=BLUE, va="center")
fig.text(0.30, 0.295, "men", fontsize=12, color=T2, va="center")
fig.text(0.54, 0.33, f"odds ratio {la.odds_ratio:.1f}", fontsize=15, weight="bold", va="center")
fig.text(0.54, 0.298, f"95% CI {la.or_low:.1f}–{la.or_high:.1f}", fontsize=11, color=T2, va="center")

expl_share = dec["explained"] / dec["gap"] * 100
fig.text(0.06, 0.23, "Decomposition: differences in industry, education, hours and sector do not explain the gap.\n"
         "Women's industry mix would even predict lower exposure. The gap comes from women and men\n"
         "doing different jobs within the same industries, mostly administrative and clerical roles.",
         fontsize=11.5, linespacing=1.45, va="top")
fig.text(0.06, 0.135, "Most workers in exposed jobs can expect AI to support their work. Reskilling should\n"
         "focus on roles where tasks may shift the most, many of them held by women.",
         fontsize=12.5, weight="bold", linespacing=1.4, va="top")
fig.text(0.06, 0.03,
         "ILO classification of GenAI potential (Gmyrek et al. 2023, WP 96, as released with the 2025 index). Potential, not job loss.\n"
         f"Employed people aged 18–66, n = {len(w):,}, weighted. Logistic regression with country fixed effects, SEs clustered by country;\n"
         "Oaxaca–Blinder decomposition (pooled reference), cluster bootstrap over countries. Source: ESS Round 11 (2023–24).\n"
         "Analysis: Tuğba G. · github.com/tugbasahingunes/neet-europe-analysis",
         fontsize=8.4, color=T2, linespacing=1.6)
fig.savefig(FIG / "genai_augmentation_automation.png", facecolor=S)
print("Done.")
