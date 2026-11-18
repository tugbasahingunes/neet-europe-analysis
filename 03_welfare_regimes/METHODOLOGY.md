# Methodology · 03 The motherhood gap across welfare regimes

## Research question
Is the motherhood gap in youth NEET (analysis 02) smaller in welfare systems with more generous family policies?

## Data and sample
Same ESS Round 11 data and variable definitions as analysis 02, restricted to **women aged 15–29**.

Countries are grouped into five welfare regimes, following the standard comparative literature (Esping-Andersen, extended with Southern and Central & Eastern European regimes):

| Regime | Countries | Women | Of whom mothers |
|---|---|---|---|
| Nordic | SE, NO, FI, IS | 398 | 34 |
| Continental | AT, BE, CH, DE, FR, NL | 873 | 86 |
| Liberal | GB, IE | 211 | 41 |
| Southern | ES, IT, PT, GR, CY | 685 | 50 |
| Central & Eastern | BG, HR, EE, HU, LT, LV, PL, SI, SK | 1,110 | 223 |

Israel, Montenegro, Serbia and Ukraine are excluded because they do not fit a standard regime classification.
Final sample: **3,277 young women in 26 countries**.

## Method
1. **Separate weighted logistic regression for each regime:**
   NEET ~ child + partner + age + age² + education + parental education + born abroad + country fixed effects
2. **Motherhood gap** = average predicted probability with child at home − without, as in analysis 02.
3. **Uncertainty:** 95% intervals from 300 bootstrap resamples of respondents within each regime.
4. **Do regimes differ?** Likelihood-ratio test comparing a pooled model with a child × regime interaction to one without it (χ², 4 df).

## Results
| Regime | No child | Mothers | Gap (95% CI) |
|---|---|---|---|
| Continental | 10% | 53% | +43 (19 to 67) |
| Nordic | 8% | 36% | +28 (6 to 65) |
| Central & Eastern | 9% | 38% | +28 (17 to 47) |
| Southern | 13% | 39% | +27 (10 to 49) |
| Liberal | 12% | 32% | +20 (1 to 48) |

- The gap is positive and its interval excludes zero in every regime.
- Differences between regimes are **not statistically significant** (LR test, p = 0.08).
- Full output: `results/results.md`.

## Limitations
- Few young mothers in some regimes (Nordic 34, Liberal 41), hence wide intervals.
- Regime grouping is a simplification; countries within a regime differ in their policies.
- Respondent-level bootstrap does not account for clustering within countries; intervals may be somewhat too narrow.
- Same causal caveats as analysis 02.
