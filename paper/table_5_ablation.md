# Table 5. Allocation Strategy Ablation

| ablation | portfolio_count | delta_cumulative_return | delta_sharpe | delta_information_ratio | delta_model_score |
| --- | --- | --- | --- | --- | --- |
| equal_weight | 19 | -0.0163 | -0.0712 | -0.1460 | -1.6421 |
| inverse_volatility | 19 | -0.0571 | -0.0660 | -0.1508 | -0.9737 |
| mean_variance | 19 | 0.0135 | -0.0115 | 0.1174 | -0.4579 |
| raw_black_litterman | 19 | -0.0188 | -0.0334 | -0.0082 | -0.3895 |
| smart_policy | 19 | -0.0194 | -0.0383 | -0.0351 | -0.6474 |
| smart_policy_oos_guard | 19 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |


Note: Deltas are strategy-level differences relative to Smart policy + OOS guard on the same allocation run. The source ablation metrics file contains 114 rows. This is a coarse allocation ablation, not a causal decomposition of every Smart-policy submodule.
