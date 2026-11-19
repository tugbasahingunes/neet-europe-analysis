# Results: what makes Europeans happy? (ESS Round 11, adults 18+)

n = 46,006 in 30 countries; weighted mean happiness 7.40 (0-10). Household income decile missing for 18.6%; imputed with chained equations (m = 5).

## Dominance analysis (Shapley decomposition of R², full R² = 0.258)

|                      |   R2_share |   percent_of_explained |
|:---------------------|-----------:|-----------------------:|
| Social relationships |      0.067 |                 25.846 |
| Health               |      0.066 |                 25.822 |
| Money                |      0.053 |                 20.618 |
| Country              |      0.032 |                 12.521 |
| Trust & safety       |      0.026 |                  9.91  |
| Demographics         |      0.008 |                  2.927 |
| Work status          |      0.004 |                  1.411 |
| Education            |      0.002 |                  0.944 |

## OLS with country fixed effects, standardised coefficients, pooled over imputations (Rubin), SEs clustered by country

|                  |   beta_std |    se |   ci_low |   ci_high |
|:-----------------|-----------:|------:|---------:|----------:|
| health           |      0.219 | 0.015 |    0.189 |     0.248 |
| income_feeling   |      0.176 | 0.015 |    0.147 |     0.205 |
| partner          |      0.153 | 0.012 |    0.13  |     0.176 |
| meet_friends     |      0.088 | 0.013 |    0.063 |     0.113 |
| social_activity  |      0.08  | 0.016 |    0.048 |     0.111 |
| trust_people     |      0.061 | 0.018 |    0.027 |     0.096 |
| close_confidants |      0.059 | 0.011 |    0.037 |     0.08  |
| feel_safe        |      0.057 | 0.017 |    0.023 |     0.091 |
| female           |      0.057 | 0.011 |    0.035 |     0.078 |
| education        |     -0.046 | 0.012 |   -0.07  |    -0.022 |
| hampered         |     -0.044 | 0.009 |   -0.062 |    -0.027 |
| discriminated    |     -0.04  | 0.008 |   -0.055 |    -0.025 |
| born_abroad      |      0.036 | 0.006 |    0.024 |     0.048 |
| child_at_home    |      0.035 | 0.007 |    0.02  |     0.049 |
| age              |      0.034 | 0.027 |   -0.019 |     0.087 |
| age2             |      0.029 | 0.01  |    0.009 |     0.049 |
| unemployed       |     -0.017 | 0.005 |   -0.027 |    -0.007 |
| retired          |      0.013 | 0.012 |   -0.01  |     0.036 |
| in_education     |      0.009 | 0.015 |   -0.021 |     0.04  |
| income_decile    |     -0.009 | 0.014 |   -0.036 |     0.018 |
| rurality         |     -0.004 | 0.009 |   -0.022 |     0.013 |

## Cross-validated R² (5-fold)

|          |    R2 |
|:---------|------:|
| OLS      | 0.253 |
| LightGBM | 0.26  |

## LightGBM mean |SHAP| (points on 0-10 scale)

|                  |   mean_abs_shap |
|:-----------------|----------------:|
| health           |           0.327 |
| income_feeling   |           0.295 |
| country          |           0.264 |
| partner          |           0.241 |
| trust_people     |           0.134 |
| meet_friends     |           0.128 |
| social_activity  |           0.109 |
| close_confidants |           0.1   |
| feel_safe        |           0.097 |
| female           |           0.097 |
| age              |           0.082 |
| hampered         |           0.051 |
| child_at_home    |           0.046 |
| education        |           0.039 |
| income_decile    |           0.038 |
| discriminated    |           0.031 |
| rurality         |           0.027 |
| born_abroad      |           0.025 |
| retired          |           0.018 |
| unemployed       |           0.017 |
| in_education     |           0.003 |

## Multilevel model

ICC (share of variance between countries, empty model): 0.085. Individual characteristics explain 72% of between-country variance and 22% of within-country variance.


## Spline partial effects (predicted happiness, all else at observed values)

|   age |   predicted |
|------:|------------:|
|    18 |        7.51 |
|    23 |        7.42 |
|    28 |        7.35 |
|    33 |        7.29 |
|    38 |        7.28 |
|    43 |        7.3  |
|    48 |        7.34 |
|    53 |        7.38 |
|    58 |        7.42 |
|    63 |        7.44 |
|    68 |        7.46 |
|    73 |        7.49 |
|    78 |        7.54 |

|   income_decile |   predicted |
|----------------:|------------:|
|               1 |        7.47 |
|               2 |        7.45 |
|               3 |        7.42 |
|               4 |        7.41 |
|               5 |        7.39 |
|               6 |        7.39 |
|               7 |        7.38 |
|               8 |        7.38 |
|               9 |        7.37 |
|              10 |        7.36 |