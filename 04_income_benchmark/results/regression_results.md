# Results: country-level NEET models

## Main model: NEET ~ log GDP per capita (excl. Türkiye)

n = 33, R² = 0.51, adj. R² = 0.49 (HC3 robust SEs)

|           |   coef |    se |   p |
|:----------|-------:|------:|----:|
| Intercept | 43.794 | 8.988 |   0 |
| log_gdp   | -7.227 | 1.967 |   0 |

## Robustness: multivariate, all countries

n = 33, R² = 0.50, adj. R² = 0.45 (HC3 robust SEs)

|               |   coef |    se |     p |
|:--------------|-------:|------:|------:|
| Intercept     | 41.568 | 9.75  | 0     |
| early_leavers |  0.289 | 0.319 | 0.364 |
| social_prot   | -0.176 | 0.161 | 0.276 |
| log_gdp       | -6.31  | 2.139 | 0.003 |

## Robustness: multivariate, excl. Türkiye

n = 32, R² = 0.45, adj. R² = 0.39 (HC3 robust SEs)

|               |   coef |    se |     p |
|:--------------|-------:|------:|------:|
| Intercept     | 38.331 | 8.479 | 0     |
| early_leavers |  0.037 | 0.275 | 0.894 |
| social_prot   | -0.051 | 0.113 | 0.651 |
| log_gdp       | -5.878 | 1.985 | 0.003 |

## Influence check (Cook's distance, multivariate model)

| geo   |   cooks_d |
|:------|----------:|
| TR    |      1.37 |
| IS    |      0.39 |
| BA    |      0.21 |
| LU    |      0.2  |
| IE    |      0.16 |

Türkiye is a highly influential observation (Cook's D = 1.37). The early-leavers and social-protection effects are not robust to excluding it, so only the income relationship is used for the headline.

## Türkiye: actual vs expected from income

|       |   actual |   expected |
|:------|---------:|-----------:|
| total |     26.3 |       13.4 |
| women |     36.8 |       14.8 |
| men   |     16.2 |       12.1 |