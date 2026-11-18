# Results: augmentation vs automation potential by gender

Employed ESS respondents aged 18-66 with an occupation code: 24,185; matched at 4 digits with complete covariates: 21,157.

## Weighted shares (%)

|              |   women |   men |
|:-------------|--------:|------:|
| augmentation |    16.5 |  14.7 |
| automation   |     6.8 |   2.8 |

## Logistic regressions (controls: age, education, industry, part-time, public sector, country; SEs clustered by country)

|              |   women |    men |   odds_ratio |   or_low |   or_high |   p |
|:-------------|--------:|-------:|-------------:|---------:|----------:|----:|
| automation   |   7.33  |  2.582 |        3.117 |    2.334 |     4.163 |   0 |
| augmentation |  14.029 | 17.449 |        0.756 |    0.688 |     0.83  |   0 |

## Oaxaca-Blinder decomposition of the automation-potential gap (women - men), percentage points

|                |   pts |   ci_low |   ci_high |   share_% |
|:---------------|------:|---------:|----------:|----------:|
| gap            |  4.08 |     3.08 |      5.41 |    100    |
| explained      | -0.88 |    -1.49 |     -0.38 |    -21.58 |
| unexplained    |  4.96 |     3.67 |      6.32 |    121.58 |
| Industry       | -1.3  |    -2.16 |     -0.61 |    -31.94 |
| Education      | -0.02 |    -0.14 |      0.16 |     -0.41 |
| Part-time work |  0.01 |    -0.15 |      0.23 |      0.33 |
| Public sector  |  0.5  |     0.24 |      0.71 |     12.31 |
| Age            |  0.01 |    -0.02 |      0.06 |      0.18 |
| Country        | -0.08 |    -0.29 |      0.04 |     -2.05 |