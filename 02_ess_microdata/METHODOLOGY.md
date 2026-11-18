# Methodology · 02 Motherhood and the gender gap

## Research question
Among young Europeans, how much of the higher NEET rate of young women is associated with having a child at home, after accounting for education, family background, age and country?

## Data
| | |
|---|---|
| Source | European Social Survey (ESS) Round 11, integrated file, edition 4.2 |
| Fieldwork | 2023–24 |
| Coverage | 30 countries (Türkiye did not take part in this round) |
| Design | Random probability samples, face-to-face interviews |
| Access | Free registration at ess.sikt.no; not redistributed in this repository |

## Sample construction
| Step | Remaining | Removed |
|---|---|---|
| All respondents | 50,116 | |
| Aged 15–29 (`agea`) | 7,457 | outside age range |
| Valid main activity (`mnactic`) | 7,389 | 68: refusal / don't know / no answer (60), "retired" (8) |
| Valid own education (`eisced` 1–7) | **7,313** | 76 |

Final analytic sample: **7,313 young people**, of whom **1,089 are NEET**.

## Variables
| Variable | Definition |
|---|---|
| **NEET** (outcome) | 1 if main activity in the last 7 days is unemployed and looking (3), unemployed not looking (4), permanently sick or disabled (5), housework / looking after children (8), or other (9). 0 if in paid work (1), education (2), or community / military service (7). |
| **Female** | `gndr` = 2 |
| **Child at home** | 1 if any household member is coded as son/daughter (`rshipa*` = 2) in the household grid |
| **Partner at home** | 1 if any household member is coded as partner/spouse (`rshipa*` = 1) |
| **Education** | ES-ISCED (`eisced`): low (1–2), medium (3–5), high (6–7; reference) |
| **Parental education** | Highest of father's and mother's ES-ISCED, same three groups; "unknown" kept as a separate category (302 cases) so that no respondents are dropped |
| **Born abroad** | `brncntr` = 2 |
| **Age** | Centred at 22, with a squared term |
| **Country** | Fixed effects (one dummy per country) |

## Method
**Weighted logistic regression:**

NEET ~ female × child + partner + age + age² + education + parental education + born abroad + country fixed effects

- **Weights:** ESS analysis weight `anweight` (combines design, post-stratification and population size), normalised to the sample size.
- **Standard errors:** clustered by country.
- **Interpretation:** odds ratios are hard to read, so results are reported as **average predicted probabilities**. Each respondent is assigned, in turn, to one of four groups (man / woman × child / no child) while keeping all other characteristics at their observed values; predicted probabilities are then averaged with the survey weights.

## Results
| Group | Predicted probability of being NEET |
|---|---|
| Young men, no child at home | 9.9% |
| Young fathers | 11.5% |
| Young women, no child at home | 10.9% |
| Young mothers | 51.4% |

- Interaction female × child: odds ratio 8.85 (95% CI 4.25–18.44, p < 0.001).
- Among NEET young mothers, **78%** (weighted) report housework or childcare as their main activity.
- Full output: `results/regression_results.md`.

## Limitations
- **Association, not causation.** Motherhood and NEET status may influence each other, and unobserved factors may affect both.
- "Child at home" comes from the household grid: it captures co-resident children, not biological parenthood, and may include a small number of step- or foster children.
- Small subgroups: 215 young men and 546 young women live with a child, so country-level breakdowns are not reliable.
- Self-reported main activity in the last 7 days.
