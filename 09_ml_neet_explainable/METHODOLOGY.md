# Methodology · 09 Machine learning for youth NEET: accuracy, explainability and fairness

## Research questions
1. How well can NEET status among young Europeans be predicted from background characteristics, and does a flexible machine-learning model outperform logistic regression?
2. Which characteristics drive the predictions?
3. If such a model were used as an **early-warning tool** to target support, would it work equally well for different groups?

This is a methodological demonstration, not a proposal to deploy individual risk scoring.

## Data
European Social Survey Round 11 (2023–24), respondents aged 15–29 with valid main activity and education: **7,313 young people in 30 countries**, of whom 1,089 are NEET (weighted rate 12.9%). Weights: ESS `anweight`, normalised.

## Features
Age; sex; own education (ES-ISCED 1–7); highest parental education; child at home; partner at home; household size; born abroad; at least one parent born abroad; place of residence (big city → farm, 1–5); father / mother not working when the respondent was 14; country.

Health, income and attitudes are deliberately **excluded**: they may be consequences of being NEET rather than predictors, and some are sensitive.

## Models
- **Logistic regression** (scikit-learn, L2-regularised, standardised features, age², country dummies, missing-value indicators with median imputation).
- **Gradient boosting** (LightGBM: 600 trees, learning rate 0.03, 15 leaves, minimum 40 cases per leaf, row and column subsampling, L2 penalty; country as a native categorical feature; missing values handled natively).
Both are trained with survey weights.

## Evaluation
- **5-fold stratified cross-validation, repeated 3 times**; all metrics computed on out-of-fold predictions and weighted.
- **ROC AUC** (ranking quality; 0.5 = random), **average precision** (precision–recall; random = base rate 0.129), **Brier score** (calibration and accuracy).

## Explainability
SHAP values (TreeExplainer) for the gradient boosting model fitted on the full sample. Global importance = mean absolute SHAP value on the log-odds scale. The contribution of "child at home" is compared between women and men who live with a child.

## Fairness audit
Scenario: an agency contacts the young people with the **top 20% of risk scores** (one common threshold). For each group: share flagged, **recall** (share of NEET young people who are flagged), false-positive rate (share of non-NEET who are flagged), and within-group AUC.

## Results
| Model | AUC | Average precision | Brier |
|---|---|---|---|
| Logistic regression | 0.727 | 0.361 | 0.098 |
| Gradient boosting | 0.732 | 0.340 | 0.102 |

- The flexible model **does not outperform** logistic regression in a meaningful way; logistic regression is slightly better on average precision and calibration.
- **Most important features (SHAP):** country, age, household size, child at home, sex, own education, mother not working at 14, parental education.
- Among those living with a child, the child raises the predicted log-odds by 1.41 for young women and 0.79 for young men.

**Fairness at the top-20% threshold:**
| Group | NEET rate | Recall | False-positive rate | AUC |
|---|---|---|---|---|
| Women | 15.7% | 57% | 14.7% | 0.77 |
| Men | 10.1% | **19%** | 10.8% | 0.68 |
| Central & Eastern | 12.4% | 51% | 8.8% | 0.78 |
| Southern | 13.6% | 41% | 15.7% | 0.75 |
| Continental | 10.7% | 39% | 10.3% | 0.75 |
| Liberal | 15.9% | 29% | 17.8% | 0.64 |
| Nordic | 8.8% | 21% | 6.8% | 0.63 |

The model would miss about **8 in 10 NEET young men**. Two reasons: men's NEET status is harder to predict from these characteristics (lower AUC), and a single threshold favours the group with the higher base rate. Group-specific thresholds or additional, more relevant information could reduce the gap, at the cost of other trade-offs.

Full output: `results/results.md`.

## Limitations
- Cross-sectional survey data with a limited set of background features; real administrative systems use different data and may perform differently.
- Region results for Nordic (n = 764) and Liberal (n = 390) countries are indicative.
- SHAP values explain the model, not causal effects.
- Hyperparameters were set a priori, not tuned; tuning is unlikely to change the conclusions given the similar performance of both models.

## Why this matters
Predictive tools are increasingly proposed for targeting social services. This analysis shows two common patterns: added model complexity may not add accuracy, and overall accuracy can hide large differences in who is missed. Group-level error analysis should be standard before any such tool is used.
