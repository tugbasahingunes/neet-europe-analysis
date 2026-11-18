# Methodology · 04 Appendix: how much does income explain?

## Research question
How much of the cross-country variation in youth NEET rates is associated with national income, and how far is each country from what its income level would predict?

## Data
| Variable | Eurostat table | Year |
|---|---|---|
| NEET rate, 15–29, total and by sex | `edat_lfse_20` | 2025 |
| GDP per capita in PPS (EU-27 = 100) | `tec00114` | 2025 |
| Early leavers from education and training, 18–24 | `edat_lfse_14` | 2025 |
| Social protection expenditure, % of GDP | `tps00098` | 2024 |
| Public education expenditure, % of GDP | `educ_uoe_fine06` | 2023 |

Sample: **34 countries** with NEET and GDP data (aggregates removed).

## Method
1. **Main model:** OLS regression of the NEET rate on log GDP per capita, estimated on 33 countries **excluding Türkiye**, with HC3 robust standard errors.
2. **Expected value:** Türkiye's predicted NEET rate from this model, compared with the actual rate; repeated separately for women and men.
3. **Robustness:** multivariate model adding early school leaving and social protection expenditure, estimated with and without Türkiye.
4. **Influence check:** Cook's distance for each country in the multivariate model.

## Results
- Log GDP per capita explains about half of the variation (R² = 0.51; coefficient −7.23, p < 0.001).
- Türkiye: actual 26.3% vs expected 13.4%. Women 36.8% vs 14.8%; men 16.2% vs 12.1%.
- Türkiye is highly influential in the multivariate model (Cook's D = 1.37). Early-leaving and social-protection effects are not robust to excluding it, so only the income model is reported.
- Full output: `results/regression_results.md`.

## Limitations
- 33 observations: limited statistical power and sensitivity to individual countries.
- The "expected" value is a simple benchmark, not a causal counterfactual.
- GDP in PPS is distorted for small financial centres (Luxembourg, Ireland); the log transformation reduces but does not remove this.
