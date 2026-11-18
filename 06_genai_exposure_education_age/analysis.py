"""
Generative AI exposure by education and age: does GenAI flip the automation story?

Data: same as analysis 05 (ILO-NASK 2025 GenAI exposure index x ESS Round 11 workers).
  - ../05_genai_exposure_gender/data/ilo_genai_exposure_isco08_2025.csv
  - ../02_ess_microdata/data/ESS11e04_2.csv

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

# ---------------------------------------------------------------- build worker file (as in 05)
occ = pd.read_csv(HERE.parent / "05_genai_exposure_gender" / "data" / "ilo_genai_exposure_isco08_2025.csv")
occ["highest"] = occ.potential25.str.contains("Gradient 4").astype(float)
occ["any"] = occ.potential25.str.contains("Gradient").astype(float)          # gradients 1-4
occ3 = occ.assign(isco3=occ.ISCO_08 // 10).groupby("isco3")[["highest", "any", "mean_score_2025"]].mean()

ess = pd.read_csv(HERE.parent / "02_ess_microdata" / "data" / "ESS11e04_2.csv", low_memory=False)
w = ess[(ess.mnactic == 1) & ess.agea.between(18, 66) & (ess.isco08 < 10000)].copy()
w["isco"] = w.isco08.astype(int)
w = w.merge(occ[["ISCO_08", "highest", "any", "mean_score_2025"]], left_on="isco", right_on="ISCO_08", how="left")
miss = w.highest.isna()
w.loc[miss, ["highest", "any", "mean_score_2025"]] = occ3.reindex(w.loc[miss, "isco"] // 10).values
w = w[w.highest.notna()].copy()
w["sex"] = w.gndr.map({1: "Men", 2: "Women"})
w["edu"] = pd.Series(np.select([w.eisced.isin([1, 2]), w.eisced.isin([3, 4, 5]), w.eisced.isin([6, 7])],
                               ["Lower secondary or less", "Upper secondary / vocational", "University"], ""), index=w.index)
w["age"] = pd.cut(w.agea, [17, 24, 34, 44, 54, 66], labels=["18–24", "25–34", "35–44", "45–54", "55–66"])
w = w[w.edu != ""]
w["w"] = w.anweight
EDU = ["Lower secondary or less", "Upper secondary / vocational", "University"]


def summary(g):
    return pd.Series({"any_exposure": np.average(g["any"], weights=g.w) * 100,
                      "highest_exposure": np.average(g.highest, weights=g.w) * 100,
                      "mean_task_score": np.average(g.mean_score_2025, weights=g.w), "n": len(g)})


by_edu = w.groupby("edu").apply(summary).reindex(EDU)
by_edu_sex = w.groupby(["edu", "sex"]).apply(summary).reindex(pd.MultiIndex.from_product([EDU, ["Women", "Men"]]))
by_age_sex = w.groupby(["age", "sex"], observed=True).apply(summary)

# bootstrap CI for highest exposure, 18-24 women vs men
rng = np.random.default_rng(7)
yg = w[w.age == "18–24"]
boot = []
for _ in range(1000):
    s = yg.sample(len(yg), replace=True, random_state=int(rng.integers(1e9)))
    f, m = s[s.sex == "Women"], s[s.sex == "Men"]
    boot.append((np.average(f.highest, weights=f.w) - np.average(m.highest, weights=m.w)) * 100)
ci = np.percentile(boot, [2.5, 97.5])

(RES / "results.md").write_text(
    "# Results: GenAI exposure by education and age (ESS Round 11 x ILO-NASK 2025)\n\n"
    f"Employed respondents aged 18-66 with occupation and education: {len(w):,}.\n\n"
    "'Any exposure' = ILO Gradients 1-4; 'highest' = Gradient 4.\n\n"
    "## By education\n\n" + by_edu.round(2).to_markdown()
    + "\n\n## By education and sex\n\n" + by_edu_sex.round(2).to_markdown()
    + "\n\n## By age and sex\n\n" + by_age_sex.round(2).to_markdown()
    + f"\n\nAges 18-24, difference women - men in highest exposure: "
      f"{(by_age_sex.loc[('18–24','Women'),'highest_exposure']-by_age_sex.loc[('18–24','Men'),'highest_exposure']):.1f} pts "
      f"(95% bootstrap CI {ci[0]:.1f} to {ci[1]:.1f}).\n")
print(by_edu.round(1)); print(by_edu_sex.round(1)); print("CI", ci.round(1))

# ---------------------------------------------------------------- figure
S, T1, T2, T3 = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
BLUE, ORANGE, GRID, LIGHT, INK = "#2a78d6", "#eb6834", "#e6e5e0", "#f2f1ed", "#3a3a37"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": T1})
fig = plt.figure(figsize=(10, 12.5), dpi=130, facecolor=S)
fig.text(0.06, 0.957, "GENERATIVE AI & WORK · 30 EUROPEAN COUNTRIES", fontsize=11.5, color=ORANGE, weight="bold")
fig.text(0.06, 0.937, "Generative AI flips the automation story:\nthe more educated you are, the more exposed",
         fontsize=22, weight="bold", va="top", linespacing=1.18)
fig.text(0.06, 0.852, "Share of workers in occupations exposed to generative AI, by education", fontsize=12, color=T2)

# panel A: any exposure by education (columns)
axA = fig.add_axes([0.08, 0.53, 0.86, 0.29], facecolor=S)
vals = by_edu.any_exposure.values
labels = ["Lower secondary\nor less", "Upper secondary /\nvocational", "University\ndegree"]
cols = ["#c9c8c1", "#8fb8ea", BLUE]
for i, (v, c) in enumerate(zip(vals, cols)):
    axA.bar(i, v, width=0.58, color=c)
    axA.text(i, v + 1.5, f"{v:.0f}%", ha="center", fontsize=22, weight="bold")
axA.set_xticks(range(3)); axA.set_xticklabels(labels, fontsize=12.5)
axA.set_ylim(0, 50); axA.set_yticks([]); axA.tick_params(length=0)
for s in axA.spines.values(): s.set_visible(False)
axA.axhline(0, color=GRID)
axA.annotate("", xy=(2.05, vals[2] + 7), xytext=(-0.05, vals[0] + 7),
             arrowprops=dict(arrowstyle="-|>", color=T3, lw=1.5, mutation_scale=14, connectionstyle="arc3,rad=-0.15"))
axA.text(1.0, max(vals) + 9.5, f"{vals[2]/vals[0]:.1f}× more exposed", ha="center", fontsize=12, color=T2)

# panel B: highest exposure, education x sex
fig.text(0.06, 0.445, "But the highest exposure sits with women in mid-level jobs", fontsize=15.5, weight="bold")
fig.text(0.06, 0.422, "Share of workers in the most exposed occupations (most tasks automatable by GenAI)",
         fontsize=11.5, color=T2)
axB = fig.add_axes([0.32, 0.20, 0.62, 0.20], facecolor=S)
y = 0
yt, yl = [], []
for e, lab in zip(EDU, ["Lower secondary or less", "Upper secondary / vocational", "University degree"]):
    for sx, col, off in (("Women", ORANGE, 0.19), ("Men", BLUE, -0.19)):
        v = by_edu_sex.loc[(e, sx), "highest_exposure"]
        axB.barh(y + off, v, height=0.34, color=col)
        axB.text(v + 0.2, y + off, f"{v:.1f}%", va="center", fontsize=11, weight="bold" if sx == "Women" else "normal")
    yt.append(y); yl.append(lab); y -= 1.15
axB.set_yticks(yt); axB.set_yticklabels(yl, fontsize=11.5)
axB.set_xlim(0, 11); axB.set_xticks([]); axB.tick_params(length=0)
for s in axB.spines.values(): s.set_visible(False)
from matplotlib.patches import Patch
axB.legend(handles=[Patch(color=ORANGE, label="women"), Patch(color=BLUE, label="men")], loc="lower right", frameon=False, fontsize=11)

# callout
yw = by_age_sex.loc[("18–24", "Women"), "highest_exposure"]; ym = by_age_sex.loc[("18–24", "Men"), "highest_exposure"]
fig.text(0.06, 0.135, f"1 in {round(100/yw)}", fontsize=30, weight="bold", color=ORANGE, va="center")
fig.text(0.27, 0.135, f"working women aged 18–24 is in one of the most exposed jobs.\nFor young men: 1 in {round(100/ym)}.",
         fontsize=12.5, va="center", linespacing=1.4)

fig.text(0.06, 0.03,
         "Exposure = ILO–NASK 2025 index (any exposure = Gradients 1–4; most exposed = Gradient 4). Technical potential, not job loss.\n"
         f"Employed people aged 18–66, n = {len(w):,}, weighted; 18–24: n = {int(by_age_sex.loc[('18–24','Women'),'n'])} women, "
         f"{int(by_age_sex.loc[('18–24','Men'),'n'])} men.\n"
         "Sources: ILO Working Paper 140 (Gmyrek et al., 2025); European Social Survey Round 11 (2023–24).\n"
         "Analysis: Tuğba G. · github.com/tugbasahingunes/neet-europe-analysis",
         fontsize=8.6, color=T2, linespacing=1.6)
fig.savefig(FIG / "genai_exposure_education.png", facecolor=S)
print("Done.")
