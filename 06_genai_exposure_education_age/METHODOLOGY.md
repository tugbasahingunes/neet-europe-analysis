# Methodology · 06 Generative AI exposure by education and age

## Research question
Which education levels and age groups in Europe work in occupations most exposed to generative AI, and how does this differ for women and men?

## Data and sample
Same data and matching as analysis 05: ILO–NASK 2025 GenAI exposure index (ISCO-08, four digits, with three-digit fallback) linked to employed ESS Round 11 respondents aged 18–66.
Respondents without a valid education code are excluded. Final sample: **23,495 workers in 30 countries**.

## Measures
- **Any exposure:** occupation in ILO Gradients 1–4.
- **Highest exposure:** occupation in Gradient 4 (most tasks could technically be performed by GenAI).
- **Education** (ES-ISCED): lower secondary or less (1–2), upper secondary / vocational (3–5), university (6–7).
- **Age groups:** 18–24, 25–34, 35–44, 45–54, 55–66.

## Method
Weighted shares (ESS `anweight`) by education, education × sex, and age × sex. For the 18–24 gender difference in highest exposure, a 95% interval from 1,000 bootstrap resamples.

## Results
| Education | Any exposure | Highest exposure |
|---|---|---|
| Lower secondary or less | 18% | 3.0% |
| Upper secondary / vocational | 33% | 5.6% |
| University | 40% | 4.9% |

- Exposure rises with education: university graduates are about 2× as likely as the least educated to work in an exposed occupation.
- The highest exposure is among women with upper secondary or vocational education (9.0%, vs 2.7% of men with the same education), reflecting clerical and administrative jobs.
- Ages 18–24: about 1 in 9 working women vs 1 in 85 working men are in the most exposed occupations. Difference 8.3 points (95% CI 4.8 to 15.7).
- Full output: `results/results.md`.

## Limitations
- Same as analysis 05: exposure is technical potential at occupation level, not a forecast of job loss.
- The 18–24 group is small (554 women, 634 men); the men's figure rests on a handful of respondents, so the ratio is indicative.
- "Flips the automation story" refers to the contrast with earlier automation research, where routine manual and low-education jobs were most exposed; this analysis does not test earlier technologies.
