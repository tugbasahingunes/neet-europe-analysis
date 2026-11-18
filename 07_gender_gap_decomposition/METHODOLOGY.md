# Methodology · 07 Decomposing the gender gap in youth NEET

## Research question
Young women in Europe are more often NEET than young men. How much of this gap is due to **differences in characteristics** (education, living with a child, age, family background, country), and how much to the **same characteristics having different consequences** for women and men?

## Data and sample
European Social Survey Round 11 (2023–24), same sample and variable definitions as analysis 02: **7,313 respondents aged 15–29 in 30 countries**. Weighted with `anweight`.

## Method: Oaxaca–Blinder decomposition
The gap in mean NEET probability between women (F) and men (M) is split into two parts:

  ȳ_F − ȳ_M = (x̄_F − x̄_M)·β\*  +  [ x̄_F·(β_F − β\*) + x̄_M·(β\* − β_M) ]
                 **explained**                       **unexplained**

- **Explained (composition) part:** how much of the gap would remain if women and men differed only in their average characteristics, valued at reference coefficients β\*.
- **Unexplained (coefficient) part:** the remainder, reflecting differences in how the same characteristics relate to NEET status for women and men (plus unobserved factors).
- **Model:** weighted linear probability model (OLS on a 0/1 outcome), which keeps the decomposition exactly additive.
- **Covariates:** child at home, partner at home, own education (low / medium; high = reference), age and age² (centred at 22), parental education (low / medium / unknown), born abroad, country fixed effects.
- **Reference coefficients β\*:** pooled model over both sexes **including a sex dummy** (Neumark 1988; Jann 2008), which avoids attributing the group difference itself to the covariates.
- **Detailed decomposition:** contributions of each covariate group to the explained part.
- **Inference:** 95% intervals from a cluster bootstrap over countries (500 replications), re-estimating everything in each replication.

A complementary analysis estimates separate models for women and men and compares the **coefficient on child at home**, with the same bootstrap.

## Results
| Component | Percentage points | 95% CI | Share of gap |
|---|---|---|---|
| Total gap (women − men) | 5.6 | 2.8 to 8.2 | 100% |
| Explained by characteristics | 1.2 | 0.1 to 2.8 | 21% |
| · Child at home | +1.4 | 0.7 to 3.3 | 26% |
| · Age | +0.6 | −0.2 to 1.2 | 10% |
| · Own education | −0.7 | −1.2 to −0.3 | −13% |
| · Other (partner, parental education, born abroad, country) | −0.1 | | |
| Unexplained | 4.4 | 2.3 to 6.3 | 79% |

**Different consequences of a child at home** (separate models, same controls):
- Young women: **+40.9 points** in NEET probability (95% CI 32.8 to 47.5)
- Young men: **+2.9 points** (95% CI −2.5 to 11.5)
- 11.6% of young women vs 6.3% of young men live with a child.

## Robustness: the index-number problem
Detailed results depend on which coefficients are used as reference. With men's coefficients, the explained part is −0.4 points (unexplained 6.0); with women's coefficients, +2.0 (unexplained 3.5). Across all three choices:
- the contribution of **education is negative** (−0.7 to −0.8): young women's higher education narrows the gap;
- the contribution of **child at home is positive** (+0.2 to +2.2);
- the **unexplained part is the larger share** of the gap (63% to 108%).

The large difference in the child-at-home coefficient between women and men is the main driver of the unexplained part. Because the size of each variable's contribution to the unexplained part depends on the choice of omitted categories, the coefficient comparison is reported instead of a detailed unexplained decomposition.

## Limitations
- Linear probability model: simple and additive, but predicted probabilities are not bounded to 0–1. A non-linear (Fairlie) decomposition could be used as a further check.
- "Unexplained" does not mean discrimination; it includes unobserved factors (e.g. preferences, local childcare availability, norms) and differences in how characteristics are measured.
- Cross-sectional data: associations, not causal effects. Living with a child and NEET status may influence each other.
- The cluster bootstrap with 30 countries gives intervals that are approximate.

## References
- Blinder, A. (1973). Wage discrimination: reduced form and structural estimates. *Journal of Human Resources*, 8(4).
- Oaxaca, R. (1973). Male–female wage differentials in urban labor markets. *International Economic Review*, 14(3).
- Neumark, D. (1988). Employers' discriminatory behavior and the estimation of wage discrimination. *Journal of Human Resources*, 23(3).
- Jann, B. (2008). The Blinder–Oaxaca decomposition for linear regression models. *The Stata Journal*, 8(4).
