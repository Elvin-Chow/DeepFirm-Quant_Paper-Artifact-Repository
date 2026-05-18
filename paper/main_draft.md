# An Auditable Explainable AI Framework for Multi-Market Tail-Risk Warning and Leakage-Guarded Bayesian Portfolio Allocation

## Abstract

Financial machine-learning systems used in portfolio risk workflows often combine opaque predictions, fragile backtests, and unclear data provenance. This paper presents DeepFirm Quant as an auditable financial ML framework rather than a new predictive model: it freezes crisis-warning artifacts, validates artifact and feature-schema hashes, records provenance and data-availability failures, prohibits sandbox substitution for paper metrics, attaches SHAP-style driver attribution, and evaluates allocation policies under leakage-guarded as-of controls. In real-data external evaluation with sandbox data disabled, the frozen warning layer produced 68,324 predictions over 19 available holdout portfolios across US, Hong Kong, China A-share, Japan, and Taiwan markets. Aggregate ROC-AUC was 0.6325 for both 1D and 5D horizons, with PR-AUC of 0.1020 and 0.0904 and top-decile lifts of 2.30 and 1.90. Threshold sensitivity changes the operational reading: a 0.60 threshold flagged only 11 rows globally and had 0.0016 recall, while lower thresholds increased recall at substantial flag-volume cost. The top 10% surveillance bucket captured 21.91% of positive events at 12.09% precision and 2.19 lift, which better supports ranking surveillance than a fixed binary crisis trigger. In allocation OOS evaluation over 19 portfolios, Smart policy with the OOS guard achieved the highest mean Sharpe ratio (1.1914) and model score (59.92) among evaluated strategies, but all strategies underperformed their benchmarks on mean excess return. The evidence supports auditability, probability-quality diagnostics, and leakage-guarded decision support, not return prediction or investment advice.

## I. Introduction

Machine-learning methods are increasingly used in financial risk and portfolio workflows, but their deployment is constrained by four recurring problems. First, many models operate as black boxes whose risk warnings cannot be inspected by portfolio managers, model validators, or compliance reviewers. Second, apparently strong backtests are often contaminated by future-data leakage, including feature construction, benchmark alignment, model selection, or decision policies that observe data beyond their stated as-of date. Third, models trained on one market or asset sleeve may generalize weakly across regional trading calendars, liquidity regimes, and provider-specific data quality. Fourth, repeated strategy search can turn historical backtests into overfit demonstrations rather than credible out-of-sample evidence [@White2000RealityCheck; @BaileyEtAl2016BacktestOverfitting; @BaileyLopezDePrado2014DeflatedSharpe; @LopezDePrado2018FinancialML].

This paper studies DeepFirm Quant as a production-oriented research stack for auditable risk warning and allocation decision support. The crisis-warning module estimates whether a submitted portfolio is approaching a future tail-risk event at 1D or 5D horizons. It does not forecast exact returns. The allocation module evaluates Bayesian portfolio weights under Smart and Professional-style controls. It is not an investment-advice system, and the reported OOS results should not be read as recommendations for any security, market, or strategy.

The central thesis is that a financial ML system can be useful even when raw predictive performance is modest, provided that it behaves like an audit contract. The system must expose provenance, validate frozen artifacts, refuse silent sandbox substitution, separate probability quality from operating thresholds, guard allocation decisions against leakage, and report weak results plainly. The paper therefore emphasizes auditability, explainability, and leakage-guarded evaluation rather than unqualified performance superiority.

The contributions are:

1. An audit-contract formulation for financial ML that maps common failure modes to framework controls and reproducible evidence artifacts.
2. A frozen multi-market tail-risk warning setup with artifact hashes, feature-schema hashes, validation status, and model-version metadata.
3. A dynamic trailing-quantile tail-event construction designed to avoid direct look-ahead labeling.
4. SHAP-style feature contribution reporting for warning explanations, grounded in the XGBoost artifact's native contribution path [@ChenGuestrin2016XGBoost; @LundbergLee2017SHAP].
5. A leakage-guarded allocation evaluation that constrains Smart policy signals to the train window and verifies policy as-of dates.
6. A real-data applied validation over US, HK, CN, JP, and TW holdout portfolios, including threshold-sensitivity and ranking-surveillance diagnostics with explicit logs for unavailable provider data rather than synthetic substitution.

## II. Related Work

### A. Financial Tail-Risk Forecasting

Market-risk measurement has long used Value at Risk and related interval forecasts, with RiskMetrics providing an influential industry reference [@JPMorganReuters1996RiskMetricsTechnicalDocument]. Coherent risk-measure theory and Expected Shortfall/CVaR motivate downside-risk measures that address limitations of quantile-only risk summaries [@ArtznerEtAl1999CoherentRisk; @RockafellarUryasev2000CVaR; @AcerbiTasche2002ExpectedShortfall]. Econometric tail-risk forecasting includes interval forecast evaluation and conditional autoregressive VaR models [@Christoffersen1998IntervalForecasts; @EngleManganelli2004CAViaR]. Recent financial ML work extends VaR and ES forecasting with forecast combinations, neural quantile regression, and neural-GARCH hybrids [@Taylor2020ForecastCombinationsVaRES; @ChronopoulosEtAl2023DeepVaR; @BuczynskiChlebus2023GARCHNet].

### B. Explainable AI for Financial Risk

Explainability is particularly important in financial risk management because decisions can affect capital allocation, risk limits, and client communication. SHAP provides additive feature-attribution explanations for model outputs [@LundbergLee2017SHAP], while LIME and broader XAI taxonomies motivate local explanations and responsible AI framing [@RibeiroSinghGuestrin2016LIME; @BarredoArrietaEtAl2020XAI]. Financial XAI work further argues for explanation mechanisms that can be inspected in fintech risk workflows [@BussmannEtAl2020XAIFintechRisk].

### C. Black-Litterman and Bayesian Allocation

Mean-variance optimization remains a foundation for portfolio construction [@Markowitz1952PortfolioSelection]. The Black-Litterman model combines equilibrium returns with investor views and view uncertainty, making it a natural Bayesian allocation layer for combining priors and model-driven signals [@BlackLitterman1992GlobalPortfolioOptimization; @SatchellScowcroft2000BlackLittermanDemystification; @Meucci2008BlackLittermanExtensions]. Recent work explores machine-learning and data-driven views within allocation pipelines [@BanElKarouiLim2018MLPortfolioOptimization; @LiEtAl2022IntelligentBlackLitterman; @BaruaSharma2022DynamicBlackLittermanMLViews; @BaruaSharma2023FearGreedMLBlackLitterman].

### D. OOS Validation and Leakage Awareness

Financial ML is especially vulnerable to overfitting because researchers can search across assets, windows, labels, and strategy variants. Data-snooping tests, deflated performance measures, and purged or embargoed validation protocols are therefore central to credible evaluation [@White2000RealityCheck; @BaileyEtAl2016BacktestOverfitting; @BaileyLopezDePrado2014DeflatedSharpe; @LopezDePrado2018FinancialML]. This paper follows the same spirit by freezing the crisis artifacts, logging data failures, and checking as-of dates for allocation decisions.

## III. Framework

### A. Data Ingestion and Provenance

The framework supports standalone US, HK, CN, JP, and TW portfolio modes. The data layer records provider source details and data-quality warnings for each experiment. Yahoo Finance chart paths are used for several markets, while China A-share data can rely on AKShare and a Yahoo fallback where supported. The paper experiments require `allow_sandbox_data=false`; when a real provider fails, the portfolio or horizon is logged as unavailable rather than replaced with synthetic data.

### B. Market Calendar Alignment

Portfolio prices are aligned by market-specific trading calendars and normalized into a common close-price contract. Benchmark returns are aligned to OOS test returns using date intersections first and only bounded forward fill where the experiment helper allows it. This avoids unbounded backfill and reduces the risk that benchmark comparisons use information unavailable on the test date.

### C. Feature Engineering

For each portfolio, the risk engine builds point-in-time features including 1D and 5D portfolio returns, rolling volatility, rolling mean return, rolling drawdown, downside volatility, skewness, kurtosis, and correlation summaries. These features are computed from historical prices up to the current date. The frozen artifacts require a 14-feature schema; feature-schema hashes are recorded in the artifact audit table.

### D. Tail-Event Label Construction

The crisis-warning target is a dynamic trailing-quantile event. At horizon `h`, the label indicates whether the future `h`-day portfolio log return falls below a shifted trailing 5% historical `h`-day return threshold. This makes the prediction target a tail-event warning rather than a point return forecast.

### E. Frozen XGBoost Crisis-Warning Artifacts

Two global artifacts are evaluated: `global_h1` and `global_h5`. The H1 artifact contains 36,849 training rows and 1,941 positive events; the H5 artifact contains 36,689 training rows and 2,102 positive events. Both cover US, HK, CN, JP, and TW and are marked globally complete, but both have `degraded_validation` status in frozen metadata. The artifact hashes are:

- H1: `b807acefbc0c5774844331b7514791fd892f33a59846250728a64ca55506d6cd`
- H5: `625482ed714b903cd94ebdfd47fc8d9b0b0e7e5282ccc6a3b9af290b537053d0`

### F. SHAP Explanations and Warning Levels

The warning layer reports calibrated crisis probability, warning level, and top feature drivers. The SHAP-style driver table uses XGBoost native contribution values for recent holdout rows. These explanations should be interpreted as model-output attributions, not causal statements about market mechanisms.

### G. Smart Allocation Policy and Leakage Guard

The allocation layer evaluates equal weight, inverse volatility, mean-variance, raw Black-Litterman, Smart policy, and Smart policy with OOS guard. Smart policy adjusts constraints and penalties from train-window risk state, regime, anomaly, and OOS diagnostics. The OOS guard checks underperformance and risk signals and may blend toward more balanced or defensive weights. In the generated allocation results, all Smart rows have `oos_leakage_guard=true`, and every `policy_asof` precedes the first test date; no as-of violations were observed.

### H. Audit-Contract Controls

The framework contribution is the control surface around the models. Table A maps the main reviewer-relevant failure modes to controls and evidence artifacts that can be inspected without trusting narrative claims.

| Failure mode | Framework control | Evidence artifact, test, or log |
|---|---|---|
| Artifact drift or silent retraining | Frozen `global_h1` and `global_h5` directories; artifact hash validation against metadata | `paper/table_1_artifact_summary.md`, `experiments/results/artifact_audit_summary.json`, `scripts/validate_crisis_warning_contract.py` |
| Feature-schema drift | Feature-schema hash validation and fixed 14-feature contract | `feature_schema_hash` fields in artifact metadata and Table 1 |
| Synthetic data substitution | Paper commands require `--allow-sandbox-data false`; provider failures are logged as skips | `experiments/paper_eval_config.yaml`, `paper/data_availability_log.md`, skipped CSV files |
| Opaque warning output | SHAP-style native XGBoost contribution rows for recent holdout observations | `experiments/results/crisis_shap_drivers.csv`, `experiments/figures/shap_top_drivers.png` |
| Future-data leakage in allocation | Train-window policy state, OOS guard flag, and `policy_asof` checks | `tests/test_oos_allocation_integrity.py`, `experiments/results/allocation_oos_metrics.csv` |
| Threshold overclaiming | Threshold grid and top-percentile ranking surveillance metrics | `experiments/results/threshold_sensitivity_metrics.csv`, `paper/table_threshold_sensitivity.md`, `experiments/figures/threshold_sensitivity.png` |
| Provider coverage gaps | Data availability log and skipped-row CSVs; no silent replacement | `paper/data_availability_log.md`, `crisis_eval_skipped.csv`, `allocation_oos_skipped.csv` |

## IV. Experimental Protocol

### A. Frozen Artifact Setup

The paper uses the existing `artifacts/crisis_warning/global_h1/` and `artifacts/crisis_warning/global_h5/` directories. The contract validation command passed before experiments:

```bash
python scripts/validate_crisis_warning_contract.py artifacts/crisis_warning/global_h1 artifacts/crisis_warning/global_h5
```

The experiment framework tests passed with 4 tests, and the crisis-warning/OOS/provenance integrity suite passed with 48 tests.

### B. Holdout Portfolio Construction

The holdout pool contains 20 portfolios, 4 per market. Exact same-market duplicate ticker-set count versus the training-domain portfolios is zero. Several portfolios share individual constituents with the training domain, with maximum within-market overlap of 3 out of 5 tickers. The evaluation is therefore portfolio-level external validation, not a zero-security-overlap transfer test.

A separate zero-security-overlap crisis-warning supplement is provided in the supplement portfolio file. It contains 10 portfolios, two per market, selected after checking frozen training-domain tickers from artifact metadata. This supplement is reported separately so the main evaluation remains comparable to the original 20-portfolio holdout design.

### C. Baselines

Crisis-warning baselines are evaluated on the final 20% of each available holdout portfolio. Logistic regression, random forest, and gradient boosting baselines are trained only on the first 80% of that portfolio's point-in-time feature rows. A historical-tail-threshold baseline predicts warning when the current historical horizon return breaches the current tail threshold. The frozen calibrated and raw XGBoost outputs are sliced to the same test windows for comparison.

Allocation baselines include equal weight, inverse volatility, mean-variance, raw Black-Litterman, Smart policy, and Smart policy with OOS guard.

### D. Metrics

Crisis-warning metrics include row count, positive event count, positive rate, ROC-AUC, PR-AUC, Brier score, log-loss, calibration error, precision and recall at 0.60, and top-decile lift. Because tail events are rare, PR-AUC and top-percentile ranking metrics are more operationally informative than ROC-AUC alone. Threshold sensitivity is computed at 0.05, 0.075, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, and 0.60, with precision, recall, F1, flag rate, flag count, and positive count reported globally, by horizon, by market, and by horizon-market group. Ranking surveillance metrics report top 1%, top 5%, and top 10% precision, recall, and lift. Allocation metrics include cumulative return, benchmark cumulative return, benchmark excess return, annualized volatility, max drawdown, Expected Shortfall, Sharpe ratio, Information Ratio, turnover, model score, and model grade.

### E. Failure Handling

Real-data provider failures are logged in `paper/data_availability_log.md`. The main crisis external evaluation skipped `cn_broad_factor_etf` for both horizons because ticker `159915` could not be fetched. The refreshed baseline comparison uses the same available real-data cache and also skips only `cn_broad_factor_etf`. Allocation OOS skipped `cn_broad_factor_etf`. These omissions are data availability limitations.

### F. Paper Tables and Figures

The manuscript uses the audit-contract map in Table A, seven generated paper tables, and seven figures. Table 1 reports frozen artifact and schema-hash validation. Table 2 reports market-level crisis metrics from 68,324 real-data holdout predictions with sandbox disabled across 1D and 5D horizons. Table 3 reports final-window baseline comparisons with the frozen artifacts sliced to the same test windows. Table 4 reports allocation OOS metrics from 19 portfolios and 42,420 return rows. Table 5 is a coarse strategy ablation over the same allocation run. Table 6 reports threshold sensitivity and top-percentile surveillance metrics from the crisis prediction CSVs. Table 7 reports cross-portfolio bootstrap uncertainty intervals over saved paper outputs; it does not retrain the frozen warning artifacts or generate additional strategy simulations.

Figure 1 (`experiments/figures/framework_architecture.png`) shows the audit-contract workflow from real-data ingestion to frozen warning artifacts, SHAP-style explanations, leakage-guarded allocation, and paper outputs. Figure 2 (`experiments/figures/roc_pr_by_horizon.png`) plots ROC and precision-recall curves for the 1D and 5D real-data holdout predictions; the precision-recall panel is the more relevant view for rare tail events. Figure 3 (`experiments/figures/calibration_by_horizon.png`) separates probability calibration from operating-threshold choice. Figure 4 (`experiments/figures/threshold_sensitivity.png`) shows precision, recall, F1, and flag rate across the threshold grid, with the 0.60 operating point marked as conservative. Figure 5 (`experiments/figures/shap_top_drivers.png`) summarizes native XGBoost contribution magnitudes for warning explanations, not causal market drivers. Figure 6 (`experiments/figures/allocation_oos_curves.png`) shows OOS allocation curves from the real-data allocation run. Figure 7 (`experiments/figures/ablation_summary.png`) summarizes the coarse allocation ablation. All figure captions should state that sandbox data is disabled and that skipped CN portfolios are logged rather than imputed.

## V. Results

### A. Artifact Audit Summary

Table 1 and Figure 1 summarize the framework audit surface. Both frozen artifacts passed hash validation. The artifact audit summary confirms that the computed H1 and H5 artifact hashes match metadata. Both artifacts are globally complete across the five target markets, but the frozen validation status is `degraded_validation`. This status is important: it supports use in an applied auditability study, but it does not support claims of strong predictive reliability.

### B. Crisis Warning External Evaluation

With sandbox data disabled and network-enabled real-market fetching, the crisis external evaluation produced 68,324 prediction rows and 2 skipped rows. Table 2 reports the market-level breakdown, and Figure 2 plots ROC and PR behavior by horizon. Aggregated over available holdout portfolios:

- H1: 34,238 rows, 1,840 positives, ROC-AUC 0.6325, PR-AUC 0.1020, Brier 0.0498, log-loss 0.2047, calibration error 0.0018, precision@0.60 0.5455, recall@0.60 0.0033, and top-decile lift 2.2988.
- H5: 34,086 rows, 1,930 positives, ROC-AUC 0.6325, PR-AUC 0.0904, Brier 0.0527, log-loss 0.2181, calibration error 0.0035, precision@0.60 0.0000, recall@0.60 0.0000, and top-decile lift 1.9013.

Table 6 and Figure 4 make the threshold problem explicit. Globally, threshold 0.05 flags 61.88% of rows and recalls 76.45% of positives, but precision is only 6.82%. Threshold 0.10 reduces the flag rate to 4.23% with precision 16.81%, recall 12.89%, and F1 14.59%. Threshold 0.20 flags only 0.79% of rows with precision 27.68% and recall 3.98%. At 0.60, the model flags only 11 of 68,324 rows; global recall falls to 0.16%, and H5 produces no flags. This is not a usable recall-sensitive crisis trigger.

The more defensible operational reading is ranking surveillance. Across both horizons, the top 1% bucket has 26.02% precision and 4.72 lift, the top 5% bucket has 15.54% precision and 2.82 lift, and the top 10% bucket has 12.09% precision, 21.91% recall, and 2.19 lift. These values support a watchlist or surveillance queue that triages high-score portfolios for review. They do not support a standalone binary alarm at 0.60.

### C. Zero-Security-Overlap Supplement

A supplemental holdout file, `experiments/portfolios/zero_overlap_supplement_portfolios.yaml`, was constructed by checking every recommended ticker against the frozen training-domain tickers in `global_h1` metadata. It contains 10 portfolios, two per market, with zero same-market security overlap. Running the frozen crisis artifacts on this supplement with sandbox disabled produced 36,114 prediction rows and zero skipped rows.

This is a crisis-warning-only supplement; baseline comparison, allocation OOS, and allocation ablation were not run for this portfolio file. The supplemental results are consistent with the main evaluation. H1 achieved ROC-AUC 0.6290, PR-AUC 0.0971, Brier 0.0480, recall@0.60 0.0043, and top-decile lift 2.3551. H5 achieved ROC-AUC 0.6139, PR-AUC 0.0895, Brier 0.0534, recall@0.60 0.0000, and top-decile lift 1.8100. At global threshold 0.10, precision was 0.1703 and recall was 0.1179; at 0.60, only 8 rows were flagged out of 36,114. This supplement reduces the ticker-overlap attack surface, but it does not change the main interpretation: ranking surveillance is better supported than a fixed binary crisis trigger.

### D. Baseline Comparison

Table 3 reports the final-20% baseline comparison, which produced 82,086 prediction rows and 300 metric rows with sandbox disabled. For H1, frozen calibrated XGBoost achieved ROC-AUC 0.6055 and PR-AUC 0.0905, while raw XGBoost achieved slightly higher ROC-AUC 0.6095 and PR-AUC 0.0992. The calibration layer substantially improved Brier score and log-loss: calibrated XGBoost had Brier/log-loss of 0.0504/0.2055, compared with 0.2084/0.6081 for raw XGBoost.

The same pattern appears at H5. Raw XGBoost had higher ROC-AUC (0.6122 versus 0.6014), but calibrated XGBoost had much better Brier/log-loss (0.0460/0.1914 versus 0.2066/0.6012). Random forest, logistic regression, gradient boosting, and historical-threshold baselines were generally below the frozen XGBoost ranking performance. The honest interpretation is that calibration improves probability quality, while raw margins can preserve stronger ranking in this sample. This distinction matters because Figure 3 evaluates probability quality, while Table 6 and Figure 4 evaluate operational threshold behavior.

### E. Calibration and Interpretability

Figure 3 and the Brier/log-loss results support the use of a probability calibration layer when the output is used as a warning probability. Calibration is not the same as selecting an operating threshold: a probability model can be reasonably calibrated while a fixed trigger still has poor recall. Figure 5 ranks the most influential features by mean absolute native contribution in the SHAP-style driver output. These drivers are useful for audit review and user communication, but they should not be interpreted as causal stress tests.

### F. Allocation OOS Performance

Table 4 and Figure 6 summarize the allocation OOS evaluation, which covered 19 portfolios, 114 strategy rows, and 42,420 return rows with sandbox disabled. Mean results across evaluated portfolios were:

- Equal weight: cumulative return 0.3763, Sharpe 1.1203, model score 58.28.
- Inverse volatility: cumulative return 0.3355, Sharpe 1.1255, model score 58.95.
- Mean-variance: cumulative return 0.4061, Sharpe 1.1799, model score 59.46.
- Raw Black-Litterman: cumulative return 0.3738, Sharpe 1.1581, model score 59.53.
- Smart policy: cumulative return 0.3732, Sharpe 1.1531, model score 59.27.
- Smart policy with OOS guard: cumulative return 0.3926, Sharpe 1.1914, model score 59.92.

Smart policy with OOS guard had the highest mean Sharpe and model score in this run, and its mean turnover (0.3701) was far below Smart policy without the guard (1.6630) and raw Black-Litterman (1.7086). Nevertheless, all strategies had negative mean benchmark excess return, with Smart policy plus guard least negative at -0.1363. This means the result supports guarded decision discipline, not benchmark outperformance.

### G. Ablation Study

Table 5 and Figure 7 summarize a strategy-level allocation ablation rather than a component-level causal decomposition. Relative to Smart policy with OOS guard, the largest mean positive cumulative-return delta among non-guard strategies came from mean-variance (+0.0135), but its model-score delta remained negative (-0.4579). Smart policy without the OOS guard had mean cumulative-return delta -0.0194 and model-score delta -0.6474. This supports the guard as a useful stabilizer in this run, though the evidence is not a causal decomposition of every Smart-policy submodule.

### H. Statistical Uncertainty

Table 7 adds percentile bootstrap intervals over portfolios, using only saved real-data outputs. For the frozen crisis-warning layer, H1 ROC-AUC was 0.6325 with a cross-portfolio interval of 0.6093 to 0.6533, while H5 ROC-AUC was 0.6325 with an interval of 0.6099 to 0.6511. PR-AUC intervals were narrower in absolute scale but remain modest: 0.0928 to 0.1130 for H1 and 0.0826 to 0.0989 for H5. Allocation intervals are wider because only 19 portfolios are available. Smart policy with OOS guard had mean Sharpe 1.1914 with interval 0.7229 to 1.7184, and mean benchmark excess return -0.1363 with interval -0.2844 to -0.0191. These intervals support the paper's framing as applied evidence for an auditable workflow rather than a claim of universal predictive or allocation superiority.

## VI. Discussion

### A. What the Framework Demonstrates

The experiments demonstrate that a multi-market financial ML workflow can be organized around frozen artifacts, hash verification, schema audit, provenance logs, explainable warning drivers, threshold-sensitivity diagnostics, and leakage-guarded allocation evaluation. The result is an auditable framework for model-risk review. It is not a claim that the chosen XGBoost artifacts or allocation policies are uniquely strong. The results also show that modest predictive signals can still be operationally informative when presented as ranking surveillance with calibration diagnostics, threshold limitations, and data availability constraints.

### B. What It Does Not Demonstrate

The paper does not demonstrate a universally superior tail-risk predictor. It does not establish alpha generation. The main holdout is not a strict zero-security-overlap transfer test, because several holdout portfolios share some constituents with training-domain portfolios. It also does not prove that Smart policy is always better than simpler allocation rules; in this run, benchmark excess return is negative for all evaluated strategies.

### C. Why Degraded Validation Still Matters

Both frozen crisis-warning artifacts have `degraded_validation` status. Rather than disqualifying the framework, this status clarifies the paper's applied contribution: the system exposes degraded validation and still allows controlled downstream evaluation. In real financial ML deployment, knowing when a model is weak, miscalibrated, or threshold-sensitive can be as important as reporting peak AUC.

### D. Deployment Implications

The 0.60 warning threshold should not be deployed as a recall-sensitive crisis trigger without recalibration, threshold tuning, or cost-sensitive evaluation. In the current real-data holdout run, it is over-conservative: it produces almost no flags globally and no H5 flags. The threshold-sensitivity table suggests that lower thresholds recover recall only by increasing flag volume, while the top-decile lift and top 1%/5% precision are more suitable for ranking-based surveillance. Any production deployment should monitor provider availability, feature-schema drift, calibration drift, threshold drift, and market-specific degradation.

### E. Financial and Ethical Limitations

The framework is a decision-support and model-risk-management tool. It should not be used as standalone investment advice. Automated allocation systems can concentrate losses, amplify model errors, and create false confidence if warnings are presented without uncertainty and provenance. Ethical deployment requires human oversight, transparent limitations, and clear separation between risk analytics and investment recommendation.

## VII. Conclusion

This paper presented an auditable explainable AI framework for multi-market tail-risk warning and leakage-guarded Bayesian portfolio allocation. Across US, HK, CN, JP, and TW holdout portfolios, frozen XGBoost artifacts produced modest crisis-warning ranking performance, while calibration improved probability quality. Threshold sensitivity showed that the default 0.60 operating point is too conservative for recall and that the evidence is better read as ranking surveillance. The allocation experiments showed that Smart policy with OOS guard improved mean Sharpe, model score, and turnover discipline relative to several baselines, but did not deliver benchmark outperformance on average. The central contribution is therefore not a claim of predictive dominance; it is a reproducible framework for auditability, explainability, leakage control, and honest applied validation.

Future work should expand the holdout pool, add richer macro and cross-asset factors, develop market-specific factor models, introduce online drift monitoring, and strengthen calibration and threshold selection under explicit cost functions.
