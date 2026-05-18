# Table 3. Crisis Baseline Comparison

| horizon | baseline | row_count | positive_event_count | roc_auc | pr_auc | brier_score | log_loss | calibration_error | precision_at_0_60 | recall_at_0_60 | top_decile_lift |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | frozen_calibrated_xgboost | 6,858 | 371.0000 | 0.6055 | 0.0905 | 0.0504 | 0.2055 | 0.0032 | 1.0000 | 0.0027 | 2.0210 |
| 1 | frozen_raw_xgboost_without_calibration | 6,858 | 371.0000 | 0.6095 | 0.0992 | 0.2084 | 0.6081 | 0.3875 | 0.1163 | 0.2022 | 2.0479 |
| 1 | gradient_boosting | 6,858 | 371.0000 | 0.5414 | 0.0594 | 0.0875 | 0.3211 | 0.0797 | 0.0520 | 0.0458 | 0.9970 |
| 1 | historical_tail_threshold | 6,858 | 371.0000 | 0.5245 | 0.0588 | 0.0967 | 2.0034 | 0.0967 | 0.1011 | 0.0997 | 1.4551 |
| 1 | logistic_regression | 6,858 | 371.0000 | 0.5558 | 0.0713 | 0.2405 | 0.6818 | 0.4113 | 0.0699 | 0.2399 | 1.4551 |
| 1 | random_forest | 6,858 | 371.0000 | 0.5759 | 0.0880 | 0.1140 | 0.3950 | 0.2311 | 0.1720 | 0.0431 | 1.7785 |
| 5 | frozen_calibrated_xgboost | 6,823 | 331.0000 | 0.6014 | 0.0642 | 0.0460 | 0.1914 | 0.0033 | 0.0000 | 0.0000 | 2.0523 |
| 5 | frozen_raw_xgboost_without_calibration | 6,823 | 331.0000 | 0.6122 | 0.0726 | 0.2066 | 0.6012 | 0.3847 | 0.0915 | 0.2024 | 1.8712 |
| 5 | gradient_boosting | 6,823 | 331.0000 | 0.5717 | 0.0605 | 0.0668 | 0.2681 | 0.0583 | 0.0824 | 0.0423 | 1.2978 |
| 5 | historical_tail_threshold | 6,823 | 331.0000 | 0.5055 | 0.0491 | 0.0898 | 1.8618 | 0.0898 | 0.0594 | 0.0574 | 1.0563 |
| 5 | logistic_regression | 6,823 | 331.0000 | 0.5501 | 0.0557 | 0.2404 | 0.6844 | 0.4008 | 0.0624 | 0.2598 | 1.0865 |
| 5 | random_forest | 6,823 | 331.0000 | 0.5706 | 0.0752 | 0.0998 | 0.3568 | 0.2047 | 0.1864 | 0.0332 | 1.7807 |


Note: Baseline rows use 82,086 real-data final-window holdout predictions with sandbox disabled. Non-frozen baselines train on the first 80% of each available portfolio and evaluate on the final 20%; frozen XGBoost is sliced to the same windows for fairness. The source baseline metrics file contains 300 rows. 2 skipped baseline-evaluation rows were logged for portfolios: cn_broad_factor_etf.
