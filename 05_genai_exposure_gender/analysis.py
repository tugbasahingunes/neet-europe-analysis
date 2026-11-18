"""
Who works in the jobs most exposed to generative AI? A gender lens on Europe.

Data
  - ILO-NASK Global Index of Occupational Exposure to GenAI, 2025 (Gmyrek et al., ILO Working Paper 140),
    occupation-level categories for 427 ISCO-08 four-digit occupations. CC BY 4.0.
    Source: https://github.com/pgmyrek/2025_GenAI_scores_ISCO08  ->  data/ilo_genai_exposure_isco08_2025.csv
  - European Social Survey Round 11 (2023-24): occupation (isco08) of employed respondents.
    Place ESS11e04_2.csv in ../02_ess_microdata/data/

Run:  python analysis.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = Path(__file__).parent
FIG, RES = HERE / "figures", HERE / "results"

# ---------------------------------------------------------------- exposure index
occ = pd.read_csv(HERE / "data" / "ilo_genai_exposure_isco08_2025.csv")
occ["highest"] = occ.potential25.str.contains("Gradient 4").astype(float)        # highest exposure
occ["high"] = occ.potential25.str.contains("Gradient 3|Gradient 4").astype(float)  # gradients 3-4
occ3 = occ.assign(isco3=occ.ISCO_08 // 10).groupby("isco3")[["highest", "high", "mean_score_2025"]].mean()

# ---------------------------------------------------------------- workers (ESS)
ess = pd.read_csv(HERE.parent / "02_ess_microdata" / "data" / "ESS11e04_2.csv", low_memory=False)
w = ess[(ess.mnactic == 1) & ess.agea.between(18, 66) & (ess.isco08 < 10000)].copy()
n_workers = len(w)
w["isco"] = w.isco08.astype(int)
w = w.merge(occ[["ISCO_08", "title", "highest", "high", "mean_score_2025"]],
            left_on="isco", right_on="ISCO_08", how="left")
matched4 = w.highest.notna().mean()
# Fallback: codes not in the index at 4 digits (e.g. reported at 3 digits) get the 3-digit average
miss = w.highest.isna()
w.loc[miss, ["highest", "high", "mean_score_2025"]] = occ3.reindex(w.loc[miss, "isco"] // 10).values
w = w[w.highest.notna()].copy()
w["female"] = (w.gndr == 2).astype(int)
w["w"] = w.anweight


def wmean(df, col):
    return np.average(df[col], weights=df.w)


share = {s: wmean(w[w.female == f], "highest") * 100 for s, f in (("women", 1), ("men", 0))}
young = w[w.agea <= 29]
share_young = {s: wmean(young[young.female == f], "highest") * 100 for s, f in (("women", 1), ("men", 0))}
top = w[w.highest == 1]
fem_in_top = wmean(top, "female") * 100
fem_all = wmean(w, "female") * 100

occs = (top.groupby(["isco", "title"])
        .apply(lambda g: pd.Series({"n": len(g), "weight": g.w.sum(), "pct_women": np.average(g.female, weights=g.w) * 100}))
        .reset_index().sort_values("weight", ascending=False))
occs = occs[occs.n >= 30]

by_country = (w.groupby(["cntry", "female"]).apply(lambda g: wmean(g, "highest") * 100)
              .unstack().rename(columns={0: "men", 1: "women"}))
n_women_higher = int((by_country.women > by_country.men).sum())

# ---------------------------------------------------------------- results
(RES / "results.md").write_text(
    "# Results: GenAI exposure by gender (ESS Round 11 x ILO-NASK 2025 index)\n\n"
    f"Employed respondents aged 18-66 with an occupation code: {n_workers:,}. "
    f"Matched at 4 digits: {matched4:.1%}; after 3-digit fallback: {len(w):,} ({len(w)/n_workers:.1%}).\n\n"
    f"- Share of workers in the highest-exposure category (Gradient 4): women {share['women']:.1f}%, men {share['men']:.1f}%.\n"
    f"- Ages 18-29: women {share_young['women']:.1f}%, men {share_young['men']:.1f}%.\n"
    f"- Women are {fem_in_top:.0f}% of workers in Gradient 4 occupations, vs {fem_all:.0f}% of all workers.\n"
    f"- Women's share is higher than men's in {n_women_higher} of {len(by_country)} countries.\n\n"
    "## Largest Gradient 4 occupations (n >= 30)\n\n" + occs.round(1).to_markdown(index=False)
    + "\n\n## By country (% of workers in Gradient 4)\n\n" + by_country.round(1).sort_values("women").to_markdown())
print(share, share_young, round(fem_in_top, 1), round(fem_all, 1), n_women_higher, len(by_country))

# ---------------------------------------------------------------- figure
S, T1, T2, T3 = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
BLUE, ORANGE, GRID, LIGHT = "#2a78d6", "#eb6834", "#e6e5e0", "#f2f1ed"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": T1})
fig = plt.figure(figsize=(10, 12.5), dpi=130, facecolor=S)

fig.text(0.06, 0.957, "GENERATIVE AI & WORK · 30 EUROPEAN COUNTRIES", fontsize=11.5, color=ORANGE, weight="bold")
fig.text(0.06, 0.937, "The jobs most exposed to generative AI\nare mostly held by women",
         fontsize=24, weight="bold", va="top", linespacing=1.15)

# waffle: 100 workers in the most exposed jobs
k_w = int(round(fem_in_top))
axw = fig.add_axes([0.06, 0.53, 0.40, 0.32]); axw.set_xlim(-0.6, 9.6); axw.set_ylim(-0.6, 9.6); axw.axis("off")
axw.set_aspect("equal")
for i in range(100):
    r, c = divmod(i, 10)
    axw.add_patch(FancyBboxPatch((c - 0.38, 9 - r - 0.38), 0.76, 0.76, boxstyle="round,pad=0,rounding_size=0.18",
                                 color=ORANGE if i < k_w else BLUE, lw=0))
fig.text(0.52, 0.80, f"{k_w}", fontsize=72, weight="bold", color=ORANGE, va="center")
fig.text(0.52, 0.735, "of every 100 workers in the jobs\nmost exposed to GenAI are women", fontsize=14, va="top", linespacing=1.35)
fig.text(0.52, 0.655, f"Women are {fem_all:.0f}% of all workers.", fontsize=13, color=T2, va="top")
fig.text(0.52, 0.605, "■", fontsize=13, color=ORANGE, va="top"); fig.text(0.545, 0.606, "women", fontsize=12, color=T2, va="top")
fig.text(0.64, 0.605, "■", fontsize=13, color=BLUE, va="top"); fig.text(0.665, 0.606, "men", fontsize=12, color=T2, va="top")

# occupations
fig.text(0.06, 0.475, "Who does these jobs?", fontsize=16, weight="bold")
fig.text(0.06, 0.452, "Share of women in the largest highest-exposure occupations", fontsize=11.5, color=T2)
show = occs.head(6).sort_values("pct_women")
axo = fig.add_axes([0.40, 0.235, 0.54, 0.20], facecolor=S)
for i, (_, r) in enumerate(show.iterrows()):
    axo.barh(i, 100, height=0.62, color=LIGHT)
    axo.barh(i, r.pct_women, height=0.62, color=ORANGE)
    axo.text(r.pct_women - 2, i, f"{r.pct_women:.0f}%", va="center", ha="right", fontsize=12, weight="bold", color="white")
axo.axvline(fem_all, color=T1, lw=1.2, ls=(0, (3, 2)))
axo.text(fem_all, len(show) - 0.35, f"{fem_all:.0f}% = women's share\nof all workers", fontsize=9, color=T2, ha="center", va="bottom")
axo.set_yticks(range(len(show)))
axo.set_yticklabels([t.replace(" Not Elsewhere Classified", " (other)").replace(" and ", " & ") for t in show.title], fontsize=11.5)
axo.set_xlim(0, 100); axo.set_xticks([]); axo.tick_params(length=0)
for s in axo.spines.values(): s.set_visible(False)

# stat strip
fig.text(0.06, 0.175, f"{share['women']:.1f}%", fontsize=30, weight="bold", color=ORANGE)
fig.text(0.06, 0.155, "of working women are in\nthe most exposed jobs", fontsize=11.5, va="top", linespacing=1.3)
fig.text(0.37, 0.175, f"{share['men']:.1f}%", fontsize=30, weight="bold", color=BLUE)
fig.text(0.37, 0.155, "of working men", fontsize=11.5, va="top")
fig.text(0.64, 0.175, f"{share_young['women']/share_young['men']:.0f}×", fontsize=30, weight="bold")
fig.text(0.64, 0.155, "gap among workers\naged 18–29", fontsize=11.5, va="top", linespacing=1.3)

fig.text(0.06, 0.03,
         "\"Most exposed\" = ILO-NASK 2025 Gradient 4: most tasks could technically be done by GenAI. Exposure ≠ job loss;\n"
         f"ILO expects transformation more than replacement. Employed people aged 18–66, n = {len(w):,}, weighted.\n"
         "Sources: ILO Working Paper 140 (Gmyrek et al., 2025); European Social Survey Round 11 (2023–24).\n"
         "Analysis: Tuğba G. · github.com/tugbasahingunes/neet-europe-analysis",
         fontsize=8.6, color=T2, linespacing=1.6)
fig.savefig(FIG / "genai_exposure_gender.png", facecolor=S)
print("Done.")
