# Paper Outline

## Title

An Auditable Explainable AI Framework for Multi-Market Tail-Risk Warning and Leakage-Guarded Bayesian Portfolio Allocation

## Abstract

- Problem: financial ML decision systems need interpretable risk warnings, leakage control, cross-market validation, and auditability.
- Method: frozen XGBoost tail-risk warning artifacts, SHAP-style explanations, provenance-aware feature construction, artifact hash/schema audit, and leakage-guarded Smart Black-Litterman allocation.
- Experiment: US, HK, CN, JP, and TW holdout portfolios; 1D and 5D dynamic trailing quantile tail-event labels; paper experiments run with sandbox data disabled.
- Results: real-data external evaluation produced 68,324 main crisis-warning predictions, a 36,114-row zero-security-overlap crisis supplement, threshold-sensitivity diagnostics, allocation OOS summaries, and cross-portfolio uncertainty intervals.
- Conclusion: emphasize auditability, explainability, leakage-guarded decision support, and applied validation rather than return prediction.

## I. Introduction

- Financial ML risk systems face four recurring problems: black-box predictions, future-data leakage, weak cross-market generalization, and backtest overfitting.
- DeepFirm Quant is framed as an auditable risk-warning and allocation-decision framework, not as an investment-advice engine or return predictor.
- Contributions:
  - Frozen multi-market tail-risk warning artifacts with schema and hash audit metadata.
  - Dynamic trailing-quantile label construction designed to avoid look-ahead leakage.
  - SHAP-style driver attribution for warning explanations.
  - Leakage-guarded out-of-sample Bayesian allocation evaluation.
  - Multi-market applied validation over US, HK, CN, JP, and TW holdout portfolios.

## II. Related Work

- Financial tail-risk forecasting.
- Explainable AI for financial risk management.
- XGBoost and tree-based financial ML.
- SHAP explanations.
- Black-Litterman and Bayesian portfolio allocation.
- VaR, Expected Shortfall, and CVaR.
- Backtest overfitting, leakage, and OOS validation.

## III. Framework

- Data ingestion and provenance.
- Market calendar alignment.
- Feature engineering for portfolio risk states.
- Tail-event label construction.
- Frozen XGBoost crisis-warning artifacts.
- SHAP explanations and warning levels.
- Artifact hash and schema audit.
- Smart allocation policy.
- Leakage-guarded OOS Black-Litterman allocation.

## IV. Experimental Protocol

- Frozen artifact setup: `global_h1` and `global_h5`.
- Holdout portfolio construction: 20 portfolios, 4 per market.
- Markets and benchmarks: US/SPY, HK/^HSI, CN/000300, JP/^N225, TW/^TWII.
- Crisis baselines: historical threshold, logistic regression, random forest, gradient boosting, frozen calibrated XGBoost artifact.
- Allocation baselines: equal weight, inverse volatility, mean-variance, raw Black-Litterman, Smart policy, Smart policy with OOS guard.
- Metrics: ROC-AUC, PR-AUC, Brier, log-loss, calibration error, precision/recall at 0.60, top-decile lift, return, volatility, drawdown, Expected Shortfall, Sharpe, Information Ratio, turnover, benchmark excess return.
- Failure handling: provider failures go to data availability log; no silent sandbox substitution.

## V. Results

- Artifact audit summary.
- Crisis warning external evaluation.
- Baseline comparison.
- Calibration and interpretability.
- Allocation OOS performance.
- Ablation study.

## VI. Discussion

- What the framework demonstrates.
- What it does not demonstrate.
- Why degraded validation still matters.
- Deployment implications.
- Financial and ethical limitations.

## VII. Conclusion

- Concise summary.
- Future work: larger holdout pool, richer macro factors, market-specific factor models, online monitoring, stronger calibration.
