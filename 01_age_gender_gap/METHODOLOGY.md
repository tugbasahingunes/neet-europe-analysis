# Methodology · 01 When does the gender gap open up?

## Research question
At what age does the gender gap in NEET rates (young people neither in employment nor in education or training) appear in European countries?

## Data
| | |
|---|---|
| Source | Eurostat, table `edat_lfse_20` (EU Labour Force Survey) |
| Indicator | NEET rate, % of the age group (`wstatus = NEMP`) |
| Breakdown | Sex (women, men) × age group (15–24, 25–29) |
| Year | 2025 |
| Access | Downloaded with the `eurostat` Python package; cached in `data/` |

For Türkiye, Eurostat's figures are based on TurkStat's Household Labour Force Survey. The 15–24 figures match TurkStat's own 2025 release within 0.2 percentage points (TurkStat: women 30.9%, men 16.3%; Eurostat: 30.7%, 16.3%).

## Processing steps
1. Keep rows with `wstatus = NEMP` (NEET) and age groups `Y15-24` and `Y25-29`.
2. Reshape to one row per country with four values: women and men, 15–24 and 25–29.
3. Drop euro-area aggregates (`EA*`, `EU28`); keep `EU27_2020` as the reference.
4. Keep countries with all four values available → **34 countries + EU-27**.

## Measures
- **Gender gap** = women's NEET rate − men's NEET rate, in percentage points, computed separately for 15–24 and 25–29.
- **Widening** = number of countries where the 25–29 gap is larger than the 15–24 gap.

## Method
Descriptive only. No model is estimated: the pattern is visible in the official aggregate figures, and explanatory analysis is done with individual-level data in analyses 02 and 03.

## Results
| | Women | Men | Gap |
|---|---|---|---|
| EU-27, 15–24 | 9.1% | 9.0% | +0.1 |
| EU-27, 25–29 | 17.8% | 11.9% | +5.9 |
| Türkiye, 15–24 | 30.7% | 16.3% | +14.4 |
| Türkiye, 25–29 | 47.4% | 16.2% | +31.2 |

The gap widens with age in **32 of 34 countries**. Full table: `results/summary.md`.

## Limitations
- Country-level aggregates: they describe patterns, not individual mechanisms.
- Cross-sectional: differences between age groups in one year are not the same as following the same people over time (cohort effects are possible).
- Small countries have larger sampling error in the LFS; Eurostat flags some values as low reliability.
