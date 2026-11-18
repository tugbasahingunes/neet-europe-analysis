# Results: country-level NEET models

## Main model: NEET ~ log GDP per capita (excl. Türkiye)

n = 33, R² = 0.49, adj. R² = 0.48 (HC3 robust SEs)

|           |   coef |    se |   p |
|:----------|-------:|------:|----:|
| Intercept | 43.537 | 8.786 |   0 |
| log_gdp   | -7.155 | 1.929 |   0 |

## Robustness: multivariate, all countries

n = 33, R² = 0.52, adj. R² = 0.47 (HC3 robust SEs)

|               |   coef |    se |     p |
|:--------------|-------:|------:|------:|
| Intercept     | 40.028 | 9.924 | 0     |
| early_leavers |  0.35  | 0.257 | 0.173 |
| social_prot   | -0.165 | 0.151 | 0.277 |
| log_gdp       | -6.163 | 2.234 | 0.006 |

## Robustness: multivariate, excl. Türkiye

n = 32, R² = 0.44, adj. R² = 0.38 (HC3 robust SEs)

|               |   coef |    se |     p |
|:--------------|-------:|------:|------:|
| Intercept     | 37.945 | 9.252 | 0     |
| early_leavers |  0.144 | 0.239 | 0.548 |
| social_prot   | -0.059 | 0.118 | 0.617 |
| log_gdp       | -5.926 | 2.144 | 0.006 |

## Influence check (Cook's distance, multivariate model)

| geo   |   cooks_d |
|:------|----------:|
| TR    |      1.02 |
| BA    |      0.24 |
| LU    |      0.21 |
| IS    |      0.2  |
| IE    |      0.13 |

Türkiye is a highly influential observation (Cook's D ≈ 1). The early-leavers and social-protection effects are not robust to excluding it, so only the income relationship is used for the headline.

## Türkiye: actual vs expected from income

|       |   actual |   expected |
|:------|---------:|-----------:|
| total |     25.9 |       13.2 |
| women |     36.4 |       14.7 |
| men   |     15.8 |       11.9 |