# Methodology · 05 Generative AI exposure through a gender lens

## Research question
Are women and men in Europe equally likely to work in the occupations most exposed to generative AI (GenAI)?

## Data
| | |
|---|---|
| Exposure index | ILO–NASK Global Index of Occupational Exposure to GenAI, 2025 (Gmyrek et al., ILO Working Paper 140). 427 ISCO-08 four-digit occupations, built from about 30,000 task scores with expert validation. Licence CC BY 4.0. Occupation-level table in `data/` |
| Workers | European Social Survey Round 11 (2023–24), 30 countries; respondents' current occupation coded in ISCO-08 (`isco08`) |

## Exposure categories (ILO–NASK 2025)
Each occupation is classified by the mean (μ) and standard deviation (σ) of its task scores (0 = task cannot be done by GenAI, 1 = could be done entirely):
- **Gradient 4 (highest exposure):** μ ≥ 0.6 and μ − σ ≥ 0.5. Most tasks in the job have high GenAI potential. This is the category labelled "most exposed" here.
- Gradients 3 to 1, minimal exposure and not exposed: progressively lower exposure.

The index measures **technical potential**, not expected job loss. ILO concludes that transformation of jobs is a more likely outcome than replacement.

## Sample construction
| Step | Remaining |
|---|---|
| ESS respondents in paid work (`mnactic` = 1), aged 18–66, with a valid occupation code | 24,185 |
| Occupation matched to the index at 4 digits | 93.3% |
| Remaining codes (reported at 3 digits) assigned the average of their 3-digit group | **23,577** (97.5%) |

For the 3-digit fallback, the "Gradient 4" indicator becomes the share of four-digit occupations in that group that are Gradient 4.

## Measures and method
- **Share of workers in Gradient 4 jobs**, by sex and by age group, weighted with the ESS analysis weight `anweight` (population-weighted across the 30 countries).
- **Women's share among Gradient 4 workers**, compared with women's share of all workers.
- **Largest Gradient 4 occupations:** occupations with at least 30 respondents, ranked by weighted size, with the weighted share of women.
- **Country breakdown:** the same shares computed within each country.

Descriptive analysis; no causal model.

## Results
- Women are **71%** of workers in Gradient 4 occupations, compared with 48% of all workers.
- 7.2% of working women vs 2.8% of working men are in Gradient 4 jobs (ratio about 2.6).
- Ages 18–29: 7.3% of women vs 1.9% of men (ratio about 4).
- Women's share in Gradient 4 jobs is higher than men's in 29 of 30 countries.
- The largest Gradient 4 occupations are clerical: general office clerks (75% women), accounting and bookkeeping clerks (88%), other clerical support workers (70%), contact centre salespersons (75%).
- Full output: `results/results.md`.

## Limitations
- Exposure is a technical measure at the occupation level; real impact depends on adoption, regulation, firms' choices and how tasks are reorganised.
- The index was built mainly from Polish task descriptions mapped to ISCO-08; tasks within the same occupation can differ between countries.
- Occupation codes in ESS are self-reported and coded by national teams; some are only available at 3 digits.
- Sample sizes for individual occupations and countries are modest; country-level figures are indicative.
