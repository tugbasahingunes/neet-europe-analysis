# Results: machine learning for youth NEET (ESS Round 11, ages 15-29)

n = 7,313; weighted NEET rate 12.9%. 5-fold stratified CV x 3 repeats, survey weights.

## Predictive performance (out-of-fold)

|       |   AUC (mean) |   AP (mean) |   Brier (mean) |   AUC (sd over repeats) |   AP (sd over repeats) |   Brier (sd over repeats) |
|:------|-------------:|------------:|---------------:|------------------------:|-----------------------:|--------------------------:|
| logit |        0.727 |       0.361 |          0.098 |                   0.001 |                  0.002 |                     0     |
| lgbm  |        0.732 |       0.34  |          0.102 |                   0.01  |                  0.007 |                     0.001 |

Average precision of a random model = base rate = 0.129.

## Global feature importance (mean |SHAP|, log-odds scale)

|                          |   mean_abs_shap |
|:-------------------------|----------------:|
| country                  |           0.484 |
| age                      |           0.417 |
| household_size           |           0.274 |
| child_at_home            |           0.248 |
| female                   |           0.202 |
| own_education            |           0.182 |
| mother_not_working_at_14 |           0.168 |
| parental_education       |           0.164 |
| rurality                 |           0.099 |
| father_not_working_at_14 |           0.09  |
| parent_born_abroad       |           0.064 |
| partner_at_home          |           0.042 |
| born_abroad              |           0.016 |

## SHAP contribution of 'child at home' among those living with a child (log-odds)

| female   |   mean_shap |
|:---------|------------:|
| men      |       0.787 |
| women    |       1.414 |

## Fairness: flagging the top 20% of risk scores (threshold 0.208)

recall = share of NEET young people who are flagged; false_positive_rate = share of non-NEET who are flagged.

|                   |    n |   NEET_rate |   flagged |   recall |   false_positive_rate |   AUC |
|:------------------|-----:|------------:|----------:|---------:|----------------------:|------:|
| All               | 7313 |       0.129 |     0.164 |    0.417 |                 0.127 | 0.738 |
| Women             | 3797 |       0.157 |     0.212 |    0.566 |                 0.147 | 0.773 |
| Men               | 3516 |       0.101 |     0.117 |    0.19  |                 0.108 | 0.68  |
| Nordic            |  764 |       0.088 |     0.08  |    0.206 |                 0.068 | 0.634 |
| Continental       | 1809 |       0.107 |     0.133 |    0.39  |                 0.103 | 0.745 |
| Liberal           |  390 |       0.159 |     0.197 |    0.294 |                 0.178 | 0.64  |
| Southern          | 1339 |       0.136 |     0.192 |    0.414 |                 0.157 | 0.75  |
| Central & Eastern | 2052 |       0.124 |     0.14  |    0.505 |                 0.088 | 0.782 |
| Other             |  959 |       0.19  |     0.259 |    0.609 |                 0.177 | 0.78  |