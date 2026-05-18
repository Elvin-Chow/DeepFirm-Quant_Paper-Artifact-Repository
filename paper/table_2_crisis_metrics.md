# Table 2. Crisis Warning External Metrics by Market

| horizon | market | roc_auc | pr_auc | brier_score | log_loss | calibration_error | precision_at_0_60 | recall_at_0_60 | top_decile_lift | positive_event_count | row_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | cn | 0.5863 | 0.0786 | 0.0451 | 0.1952 | 0.0044 | 0.5000 | 0.0074 | 1.9485 | 272.0000 | 5,700 |
| 1 | hk | 0.5984 | 0.0946 | 0.0508 | 0.2095 | 0.0016 | 0.0000 | 0.0000 | 2.2192 | 315.0000 | 5,782 |
| 1 | jp | 0.6391 | 0.1025 | 0.0506 | 0.2041 | 0.0033 | 0.0000 | 0.0000 | 2.5045 | 431.0000 | 7,886 |
| 1 | tw | 0.6348 | 0.1057 | 0.0530 | 0.2123 | 0.0056 | 1.0000 | 0.0026 | 2.5165 | 385.0000 | 6,702 |
| 1 | us | 0.6730 | 0.1249 | 0.0491 | 0.2024 | 0.0021 | 0.6000 | 0.0069 | 2.4937 | 437.0000 | 8,168 |
| 5 | cn | 0.6268 | 0.0815 | 0.0458 | 0.1900 | 0.0062 | 0.0000 | 0.0000 | 2.2006 | 277.0000 | 5,676 |
| 5 | hk | 0.5699 | 0.0959 | 0.0533 | 0.2240 | 0.0053 | 0.0000 | 0.0000 | 2.1212 | 330.0000 | 5,750 |
| 5 | jp | 0.6339 | 0.0932 | 0.0552 | 0.2339 | 0.0072 | 0.0000 | 0.0000 | 2.2895 | 467.0000 | 7,854 |
| 5 | tw | 0.6526 | 0.0944 | 0.0564 | 0.2233 | 0.0088 | 0.0000 | 0.0000 | 2.1287 | 404.0000 | 6,670 |
| 5 | us | 0.6611 | 0.0949 | 0.0517 | 0.2139 | 0.0037 | 0.0000 | 0.0000 | 2.0786 | 452.0000 | 8,136 |


Note: Metrics use 68,324 real-data holdout predictions with sandbox disabled across 1D and 5D horizons. 2 skipped crisis-warning rows were logged for portfolios: cn_broad_factor_etf. PR-AUC is emphasized alongside ROC-AUC because tail events are rare.
