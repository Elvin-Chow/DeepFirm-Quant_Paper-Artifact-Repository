# Table 7. Cross-Portfolio Uncertainty Summary

| task | group | metric | point_estimate | ci_lower | ci_upper | unit_count | row_count | n_bootstrap | method |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| allocation | equal_weight | benchmark_excess_return | -0.1526 | -0.2607 | -0.0290 | 19 | 19 | 500 | portfolio bootstrap percentile CI over saved OOS metric rows |
| allocation | equal_weight | model_score | 58.2789 | 53.7918 | 62.6905 | 19 | 19 | 500 | portfolio bootstrap percentile CI over saved OOS metric rows |
| allocation | equal_weight | sharpe | 1.1203 | 0.6804 | 1.7249 | 19 | 19 | 500 | portfolio bootstrap percentile CI over saved OOS metric rows |
| allocation | inverse_volatility | benchmark_excess_return | -0.1934 | -0.3236 | -0.0675 | 19 | 19 | 500 | portfolio bootstrap percentile CI over saved OOS metric rows |
| allocation | inverse_volatility | model_score | 58.9474 | 52.8846 | 63.8063 | 19 | 19 | 500 | portfolio bootstrap percentile CI over saved OOS metric rows |
| allocation | inverse_volatility | sharpe | 1.1255 | 0.6678 | 1.6284 | 19 | 19 | 500 | portfolio bootstrap percentile CI over saved OOS metric rows |
| allocation | mean_variance | benchmark_excess_return | -0.1228 | -0.2650 | 0.0222 | 19 | 19 | 500 | portfolio bootstrap percentile CI over saved OOS metric rows |
| allocation | mean_variance | model_score | 59.4632 | 53.7747 | 64.5650 | 19 | 19 | 500 | portfolio bootstrap percentile CI over saved OOS metric rows |
| allocation | mean_variance | sharpe | 1.1799 | 0.7092 | 1.7992 | 19 | 19 | 500 | portfolio bootstrap percentile CI over saved OOS metric rows |
| allocation | raw_black_litterman | benchmark_excess_return | -0.1551 | -0.2926 | -0.0299 | 19 | 19 | 500 | portfolio bootstrap percentile CI over saved OOS metric rows |
| allocation | raw_black_litterman | model_score | 59.5316 | 54.5228 | 64.2830 | 19 | 19 | 500 | portfolio bootstrap percentile CI over saved OOS metric rows |
| allocation | raw_black_litterman | sharpe | 1.1581 | 0.7008 | 1.7749 | 19 | 19 | 500 | portfolio bootstrap percentile CI over saved OOS metric rows |
| allocation | smart_policy | benchmark_excess_return | -0.1557 | -0.2897 | -0.0232 | 19 | 19 | 500 | portfolio bootstrap percentile CI over saved OOS metric rows |
| allocation | smart_policy | model_score | 59.2737 | 54.2629 | 64.1968 | 19 | 19 | 500 | portfolio bootstrap percentile CI over saved OOS metric rows |
| allocation | smart_policy | sharpe | 1.1531 | 0.7033 | 1.8442 | 19 | 19 | 500 | portfolio bootstrap percentile CI over saved OOS metric rows |
| allocation | smart_policy_oos_guard | benchmark_excess_return | -0.1363 | -0.2844 | -0.0191 | 19 | 19 | 500 | portfolio bootstrap percentile CI over saved OOS metric rows |
| allocation | smart_policy_oos_guard | model_score | 59.9211 | 55.2555 | 65.1578 | 19 | 19 | 500 | portfolio bootstrap percentile CI over saved OOS metric rows |
| allocation | smart_policy_oos_guard | sharpe | 1.1914 | 0.7229 | 1.7184 | 19 | 19 | 500 | portfolio bootstrap percentile CI over saved OOS metric rows |
| crisis_warning | horizon_1d | brier_score | 0.0498 | 0.0482 | 0.0514 | 19 | 34238 | 500 | portfolio bootstrap percentile CI over saved frozen-artifact predictions |
| crisis_warning | horizon_1d | log_loss | 0.2047 | 0.1996 | 0.2095 | 19 | 34238 | 500 | portfolio bootstrap percentile CI over saved frozen-artifact predictions |
| crisis_warning | horizon_1d | pr_auc | 0.1020 | 0.0928 | 0.1130 | 19 | 34238 | 500 | portfolio bootstrap percentile CI over saved frozen-artifact predictions |
| crisis_warning | horizon_1d | roc_auc | 0.6325 | 0.6093 | 0.6533 | 19 | 34238 | 500 | portfolio bootstrap percentile CI over saved frozen-artifact predictions |
| crisis_warning | horizon_1d | top_decile_lift | 2.2988 | 2.0902 | 2.5203 | 19 | 34238 | 500 | portfolio bootstrap percentile CI over saved frozen-artifact predictions |
| crisis_warning | horizon_5d | brier_score | 0.0527 | 0.0509 | 0.0545 | 19 | 34086 | 500 | portfolio bootstrap percentile CI over saved frozen-artifact predictions |
| crisis_warning | horizon_5d | log_loss | 0.2181 | 0.2087 | 0.2283 | 19 | 34086 | 500 | portfolio bootstrap percentile CI over saved frozen-artifact predictions |
| crisis_warning | horizon_5d | pr_auc | 0.0904 | 0.0826 | 0.0989 | 19 | 34086 | 500 | portfolio bootstrap percentile CI over saved frozen-artifact predictions |
| crisis_warning | horizon_5d | roc_auc | 0.6325 | 0.6099 | 0.6511 | 19 | 34086 | 500 | portfolio bootstrap percentile CI over saved frozen-artifact predictions |
| crisis_warning | horizon_5d | top_decile_lift | 1.9013 | 1.8472 | 2.3705 | 19 | 34086 | 500 | portfolio bootstrap percentile CI over saved frozen-artifact predictions |


Note: Uncertainty intervals are 2.5th to 97.5th percentile cross-portfolio bootstrap intervals over saved real-data outputs. Crisis rows resample portfolios within each horizon without retraining frozen artifacts. Allocation rows resample portfolio-level OOS metric rows within each strategy. Wide intervals should be read as limited applied evidence, not universal superiority.
