# Results: ESS Round 11 NEET model

Sample: 7313 respondents aged 15-29, 30 countries.

Weighted NEET rate: men 10.1%, women 15.7%.

## Logistic regression (odds ratios; country fixed effects not shown; SEs clustered by country)

|                                          |   odds_ratio |   ci_low |   ci_high |     p |
|:-----------------------------------------|-------------:|---------:|----------:|------:|
| Intercept                                |        0.083 |    0.058 |     0.119 | 0     |
| C(edu, Treatment('high'))[T.low]         |        3.018 |    2.145 |     4.246 | 0     |
| C(edu, Treatment('high'))[T.mid]         |        1.4   |    1.053 |     1.863 | 0.021 |
| C(par_edu, Treatment('high'))[T.low]     |        1.549 |    0.979 |     2.452 | 0.061 |
| C(par_edu, Treatment('high'))[T.mid]     |        1.172 |    0.953 |     1.443 | 0.133 |
| C(par_edu, Treatment('high'))[T.unknown] |        2.847 |    1.463 |     5.537 | 0.002 |
| female                                   |        1.125 |    0.87  |     1.453 | 0.369 |
| child                                    |        1.194 |    0.57  |     2.504 | 0.638 |
| female:child                             |        8.85  |    4.248 |    18.44  | 0     |
| partner                                  |        0.738 |    0.497 |     1.094 | 0.13  |
| age_c                                    |        1.12  |    1.065 |     1.178 | 0     |
| I(age_c ** 2)                            |        0.975 |    0.964 |     0.985 | 0     |
| abroad                                   |        1.333 |    1.112 |     1.597 | 0.002 |

## Average predicted probability of being NEET

|                               |   percent |
|:------------------------------|----------:|
| Young men, no child at home   |       9.9 |
| Young fathers                 |      11.5 |
| Young women, no child at home |      10.9 |
| Young mothers                 |      51.4 |

Share of NEET young mothers whose main activity is housework/childcare: 78%

## Unweighted cell counts

|                       |   NEET |   not NEET |
|:----------------------|-------:|-----------:|
| ('men', 'child')      |     34 |        181 |
| ('men', 'no child')   |    355 |       2946 |
| ('women', 'child')    |    303 |        243 |
| ('women', 'no child') |    397 |       2854 |