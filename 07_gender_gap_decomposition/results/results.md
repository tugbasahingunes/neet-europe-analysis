# Results: Oaxaca-Blinder decomposition of the gender gap in youth NEET

Sample: 7,313 respondents aged 15-29, 30 countries (ESS Round 11). Weighted NEET rate: women 15.7%, men 10.1%.

Positive contributions widen the gap (women more likely NEET); negative ones narrow it.

## Main decomposition (pooled reference, 95% cluster-bootstrap CI over countries, 500 replications)

|                    |   estimate_pts |   ci_low |   ci_high |   share_of_gap_% |
|:-------------------|---------------:|---------:|----------:|-----------------:|
| gap                |           5.56 |     2.84 |      8.15 |           100    |
| explained          |           1.17 |     0.07 |      2.81 |            21.09 |
| unexplained        |           4.39 |     2.3  |      6.3  |            78.91 |
| Child at home      |           1.44 |     0.71 |      3.26 |            25.84 |
| Partner at home    |          -0.34 |    -0.81 |      0.14 |            -6.17 |
| Own education      |          -0.74 |    -1.18 |     -0.33 |           -13.36 |
| Age                |           0.57 |    -0.18 |      1.19 |            10.22 |
| Parental education |           0.14 |    -0.12 |      0.31 |             2.52 |
| Born abroad        |          -0    |    -0.06 |      0.04 |            -0.03 |
| Country            |           0.11 |     0    |      0.23 |             2.07 |

## Robustness: choice of reference coefficients (percentage points)

|                    |   pooled (main) |   men's coefficients |   women's coefficients |
|:-------------------|----------------:|---------------------:|-----------------------:|
| gap                |            5.56 |                 5.56 |                   5.56 |
| explained          |            1.17 |                -0.44 |                   2.04 |
| unexplained        |            4.39 |                 6    |                   3.51 |
| Child at home      |            1.44 |                 0.15 |                   2.16 |
| Partner at home    |           -0.34 |                -0.45 |                  -0.31 |
| Own education      |           -0.74 |                -0.74 |                  -0.81 |
| Age                |            0.57 |                 0.35 |                   0.81 |
| Parental education |            0.14 |                 0.14 |                   0.11 |
| Born abroad        |           -0    |                -0    |                  -0    |
| Country            |            0.11 |                 0.1  |                   0.09 |

## Same characteristic, different consequence: child at home

Coefficients from separate weighted linear probability models for women and men (same controls).

|                                              |   estimate |   ci_low |   ci_high |
|:---------------------------------------------|-----------:|---------:|----------:|
| Effect of child at home on NEET, women (pts) |       40.9 |     32.8 |      47.5 |
| Effect of child at home on NEET, men (pts)   |        2.9 |     -2.5 |      11.5 |
| Share living with a child, women (%)         |       11.6 |      9.2 |      14.6 |
| Share living with a child, men (%)           |        6.3 |      4   |       8   |