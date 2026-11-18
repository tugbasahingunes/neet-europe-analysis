# Methodology · 08 Will generative AI help or replace? Augmentation vs automation by gender

## Research questions
1. Are women and men equally likely to work in jobs where generative AI is expected mainly to **support** the work (augmentation) versus jobs where it could **take over many tasks** (automation)?
2. Does the gender gap in automation potential remain among women and men with the same age, education, industry, working hours, sector and country?
3. How much of the gap is explained by differences in these characteristics?

## Data
| | |
|---|---|
| Occupation classification | ILO classification of GenAI potential from Gmyrek et al. (2023), ILO Working Paper 96, included as `potential23` in the 2025 ILO–NASK release (CC BY 4.0). Categories: Augmentation potential, Automation potential, "Big unknown", Not affected |
| Workers | European Social Survey Round 11 (2023–24), 30 countries |

The 2023 classification is used because it separates augmentation from automation explicitly; the 2025 index (analyses 05–06) uses exposure gradients instead.

## Sample
| Step | Remaining |
|---|---|
| Employed (`mnactic` = 1), aged 18–66, valid ISCO-08 code | 24,185 |
| Occupation matched at four digits (categories are not averaged at three digits) and complete covariates | **21,157** |

## Variables
- **Outcomes:** automation potential (0/1), augmentation potential (0/1).
- **Covariates:** female; age and age² (centred at 42); education (ES-ISCED low / medium / high); industry (NACE Rev. 2 grouped into 8 broad sectors; reference: ICT, finance and professional services); part-time (< 30 usual weekly hours, `wkhtot`); public sector (`tporgwk` 1–3); country fixed effects.
- **Weights:** ESS `anweight`, normalised.

## Methods
1. **Weighted shares** of workers in each category, by sex.
2. **Weighted logistic regressions** of each outcome on the covariates; standard errors clustered by country. Results reported as the odds ratio for women and as **average predicted probabilities** with sex set to female or male for all workers.
3. **Two-fold Oaxaca–Blinder decomposition** of the women–men gap in automation potential, using a weighted linear probability model and pooled reference coefficients including a sex dummy (Neumark/Jann). 95% intervals from a cluster bootstrap over countries (300 replications).

## Results
| | Women | Men |
|---|---|---|
| Augmentation potential (raw) | 16.5% | 14.7% |
| Automation potential (raw) | 6.8% | 2.8% |
| Automation potential, same characteristics | 7.3% | 2.6% |
| Augmentation potential, same characteristics | 14.0% | 17.5% |

- Automation potential: odds ratio for women **3.1** (95% CI 2.3–4.2).
- Augmentation potential: odds ratio for women 0.76 (95% CI 0.69–0.83). In raw terms women and men are similar; with the same characteristics, men are somewhat more likely to be in augmentation-potential jobs.
- **Decomposition** of the 4.1-point automation gap: the explained part is negative (−0.9 points, 95% CI −1.5 to −0.4). Women's industry mix would predict *lower* automation potential (−1.3 points); working in the public sector adds +0.5. The gap is therefore not explained by industry, education, hours or sector; it reflects different occupations within the same industries, mostly administrative and clerical roles.
- Full output: `results/results.md`.

## Limitations
- The ILO categories describe **potential**, not forecasts of job loss. Most jobs are expected to be transformed rather than replaced.
- The 2023 classification predates the 2025 refinement; category boundaries may have shifted for some occupations.
- Industry is coarse (8 groups); a finer industry breakdown could explain more of the gap.
- Cross-sectional; associations only.
