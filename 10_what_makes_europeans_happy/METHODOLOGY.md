# Methodology · 10 What makes Europeans happy?

## Research question
Which aspects of people's lives account for the differences in happiness among European adults, and are the answers robust across different analytical methods?

## Data
European Social Survey Round 11 (2023–24), 30 countries. Adults aged 18+ with a valid happiness score and complete core covariates: **n = 46,006**. Weights: ESS `anweight`, normalised. Türkiye did not take part in this round.

**Outcome:** "Taking all things together, how happy would you say you are?" (0 = extremely unhappy, 10 = extremely happy).

## Predictors (grouped)
| Group | Variables |
|---|---|
| Health | self-rated health (1–5), hampered in daily activities by illness or disability (0–2) |
| Social relationships | how often meets socially (1–7), number of people to discuss intimate matters with (0–6), social activities compared with others (1–5), lives with partner |
| Money | household income decile (1–10), feeling about household income (1 = very difficult … 4 = living comfortably) |
| Trust & safety | trust in people (0–10), feeling safe walking alone after dark (1–4), member of a group discriminated against |
| Work status | unemployed, retired, in education (reference: all others) |
| Demographics | age, age², sex, born abroad, child at home, rurality |
| Education | ES-ISCED (1–7) |
| Country | country fixed effects |

Political attitudes and religiosity are deliberately excluded.

## Methods
1. **Multiple imputation.** Household income decile is missing for 18.6% of respondents. It is imputed with chained equations (scikit-learn `IterativeImputer`, Bayesian ridge, posterior sampling), creating **5 completed data sets**, using all predictors and country dummies.
2. **OLS with country fixed effects.** Weighted regression of happiness on all predictors, with outcome and predictors standardised; standard errors clustered by country. Estimates are combined across imputations with **Rubin's rules**.
3. **Dominance analysis.** Shapley decomposition of R² across the 8 predictor groups: each group's average incremental contribution to R² over all 128 possible orderings of the other groups (Budescu 1993; Azen & Budescu 2003).
4. **Natural cubic splines.** Age (5 df) and income decile (4 df) entered as splines with all other predictors; partial effects computed as average predictions with the variable set to each value.
5. **Gradient boosting + SHAP.** LightGBM regression with the same predictors (country as a categorical feature); 5-fold cross-validated R² compared with OLS; global importance from mean absolute SHAP values.
6. **Multilevel model.** Random-intercept models (individuals within countries): an empty model gives the intraclass correlation (ICC); adding individual predictors shows how much of the between-country variance they account for.

## Results
**Dominance analysis** (full R² = 0.26):

| Group | Share of explained variance |
|---|---|
| Social relationships | 26% |
| Health | 26% |
| Money | 21% |
| Country | 13% |
| Trust & safety | 10% |
| Demographics | 3% |
| Work status | 1% |
| Education | 1% |

**Strongest individual predictors** (standardised β, 95% CI): self-rated health 0.22 (0.19–0.25); feeling about household income 0.18 (0.15–0.21); living with a partner 0.15 (0.13–0.18); meeting socially 0.09; social activity 0.08; trust in people 0.06; number of confidants 0.06; feeling safe 0.06.

- **Income level vs financial security:** once the feeling about household income and other factors are included, the income decile has no independent association (β = −0.01, CI −0.04 to 0.02). The money group's contribution comes almost entirely from the sense of getting by.
- **Age:** with other factors held equal, predicted happiness follows a shallow U-shape, lowest at age 37 (7.28) and highest at 80 (7.56). The difference is small (about 0.3 points on a 0–10 scale).
- **Children at home:** small positive association (β = 0.04, CI 0.02–0.05).
- **Gradient boosting:** cross-validated R² 0.26 vs 0.25 for OLS, with the same leading drivers (health, feeling about income, partner, country).
- **Multilevel:** 8.5% of the variance in happiness lies between countries; individual characteristics account for 72% of that between-country variance and 22% of within-country variance.

Full output: `results/results.md`.

## Limitations
- Cross-sectional associations; happiness can also influence health, relationships and perceived financial security (reverse causality).
- The feeling about income partly captures needs and expectations as well as income; it is strongly related to the income decile, so their separate effects should be interpreted with care.
- Single-item happiness measure; responses may vary with cultural response styles, which country fixed effects only partly address.
- Imputation assumes income is missing at random conditional on the observed predictors.

## References
- Azen, R. & Budescu, D. (2003). The dominance analysis approach for comparing predictors in multiple regression. *Psychological Methods*, 8(2).
- Budescu, D. (1993). Dominance analysis: a new approach to the problem of relative importance of predictors. *Psychological Bulletin*, 114(3).
- Rubin, D. (1987). *Multiple Imputation for Nonresponse in Surveys*. Wiley.
- Lundberg, S. & Lee, S.-I. (2017). A unified approach to interpreting model predictions. *NeurIPS*.
