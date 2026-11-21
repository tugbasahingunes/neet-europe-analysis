# Methodology · 11 Finland and generative AI

## Research questions
1. How does generative AI use in Finland differ from the rest of Europe, especially by age?
2. Is Finland's high adult use unusual, or is it what its skills and education levels would predict?
3. Are Finnish workers more or less likely to work in jobs exposed to generative AI?

## Data
| Indicator | Source | Year |
|---|---|---|
| Used generative AI tools in the last 3 months, % of individuals, by age, sex, purpose | Eurostat `isoc_ai_iaiu` | 2025 (first year collected) |
| Basic or above basic overall digital skills, ages 25–54 (`I_DSK2_BAB`) | Eurostat `isoc_sk_dskl_i21` | 2025 |
| Participation in education and training in the last 4 weeks, ages 25–64 | Eurostat `trng_lfse_01` | 2025 |
| Tertiary attainment (ISCED 5–8), ages 25–64 | Eurostat `edat_lfse_03` | 2025 |
| GDP per capita in PPS | Eurostat `tec00114` | 2025 |
| Occupation of employed respondents | European Social Survey Round 11 | 2023–24 |
| GenAI potential by occupation | ILO (Gmyrek et al. 2023; ILO–NASK 2025) | |

## Methods
1. **Age profiles:** GenAI use for six age groups, Finland vs EU-27. **Youth–adult gap** = use at 16–24 minus use at 25–54, for all 35 countries with data.
2. **Cross-country model:** OLS of GenAI use among 25–54-year-olds on digital skills, adult learning participation, tertiary attainment and log GDP per capita, for 33 countries with complete data; HC3 robust standard errors; standardised coefficients. Predictive fit checked with **leave-one-out** predictions (each country predicted from a model estimated without it). Finland's actual value is compared with its leave-one-out prediction.
3. **Exposure:** employed ESS respondents aged 18–66 matched to ILO occupational categories at four digits; weighted shares for Finland (n = 708) and all other ESS countries (n = 21,850); 95% intervals from 500 bootstrap resamples.

## Results
- GenAI use, 16–74: **Finland 46%**, EU-27 33%. Work-related use: Finland 25%, EU 15%.
- By age: 16–24 Finland 67% vs EU 64%; **45–54 Finland 52% vs EU 28%**.
- **Youth–adult gap:** Finland 9 points, the smallest of 35 countries; EU-27 25 points.
- **Cross-country model** (standardised β): digital skills 0.46 (p < 0.001), tertiary attainment 0.47 (p = 0.001), adult learning 0.21 (n.s.), log GDP −0.15 (n.s.). R² = 0.72; leave-one-out R² = 0.68. **Finland: predicted 57%, actual 58%**, close to what its skills and education predict.
- **Exposure:** jobs where AI can mainly support the work: Finland 16.5% (13.4–19.6) vs 15.5% (14.6–16.4). Most exposed jobs (ILO 2025 Gradient 4): **Finland 2.0% (1.1–3.2) vs 5.0% (4.5–5.5)**. Automation potential (ILO 2023): Finland 3.3% (1.9–4.6) vs 4.8% (4.3–5.2).

Full output: `results/results.md`.

## Limitations
- 2025 is the first year Eurostat measured GenAI use; no trend yet.
- Country-level model with 33 observations: an association across countries, not a causal effect; digital skills and education are strongly correlated.
- Self-reported use; "use in the last 3 months" does not measure intensity.
- Finnish ESS worker sample is modest; intervals are reported.
