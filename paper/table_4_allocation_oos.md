# Table 4. Allocation OOS Performance

| strategy | portfolio_count | cumulative_return | annualized_volatility | max_drawdown | expected_shortfall | sharpe | information_ratio | turnover | benchmark_excess_return | model_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| equal_weight | 19 | 0.3763 | 0.2226 | -0.1974 | -0.0524 | 1.1203 | -0.4597 | 0.0000 | -0.1526 | 58.2789 |
| inverse_volatility | 19 | 0.3355 | 0.2235 | -0.1955 | -0.0538 | 1.1255 | -0.4645 | 0.3152 | -0.1934 | 58.9474 |
| mean_variance | 19 | 0.4061 | 0.2389 | -0.2082 | -0.0560 | 1.1799 | -0.1963 | 2.4759 | -0.1228 | 59.4632 |
| raw_black_litterman | 19 | 0.3738 | 0.2200 | -0.1937 | -0.0520 | 1.1581 | -0.3219 | 1.7086 | -0.1551 | 59.5316 |
| smart_policy | 19 | 0.3732 | 0.2201 | -0.1939 | -0.0520 | 1.1531 | -0.3488 | 1.6630 | -0.1557 | 59.2737 |
| smart_policy_oos_guard | 19 | 0.3926 | 0.2192 | -0.1919 | -0.0517 | 1.1914 | -0.3138 | 0.3701 | -0.1363 | 59.9211 |


Note: Values are means across 19 real-data holdout portfolios, 114 strategy rows, and 42,420 OOS return rows with sandbox disabled. 1 skipped allocation rows were logged for portfolios: cn_broad_factor_etf. Benchmark excess return remains negative for every listed strategy.
