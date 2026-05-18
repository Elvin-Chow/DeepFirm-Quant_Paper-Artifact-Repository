# Related Work Notes

Verification date: 2026-05-18 HKT. Citation keys refer to `paper/references.bib`.

## Core Methods

- `BlackLitterman1992GlobalPortfolioOptimization`: Original Black-Litterman article for combining equilibrium expected returns with investor views and view confidence. This is the anchor citation for the paper's Bayesian allocation module and "views" terminology.
- `LundbergLee2017SHAP`: Original SHAP paper. Use for the claim that additive feature attribution can give local feature-importance explanations for complex models.
- `ChenGuestrin2016XGBoost`: Original XGBoost systems paper. Use for the frozen gradient-boosted tree crisis-warning artifacts and scalability/regularized tree boosting background.

## VaR, Expected Shortfall, and CVaR

- `JPMorganReuters1996RiskMetricsTechnicalDocument`: Foundational VaR industry technical document; useful for explaining historical market-risk measurement lineage. No DOI found, so the entry is a verified manual/book-style record.
- `ArtznerEtAl1999CoherentRisk`: Defines coherent risk-measure axioms and motivates why tail-risk measures need properties beyond simple quantiles.
- `RockafellarUryasev2000CVaR`: Foundational CVaR/conditional value-at-risk optimization source. Use when describing Expected Shortfall/CVaR as an optimization-compatible downside-risk metric.
- `AcerbiTasche2002ExpectedShortfall`: Supports the coherence of Expected Shortfall, useful when contrasting ES/CVaR with VaR.
- `Christoffersen1998IntervalForecasts`: Provides interval forecast evaluation methods relevant to VaR exceedance/backtesting logic.
- `EngleManganelli2004CAViaR`: Financial VaR forecasting baseline that models conditional quantiles directly; useful as an econometric comparator to ML tail-risk warning.

## Financial ML Risk Forecasting

- `Taylor2020ForecastCombinationsVaRES`: Directly addresses joint forecasting of VaR and Expected Shortfall and forecast combinations.
- `ChronopoulosEtAl2023DeepVaR`: Supports neural-network quantile regression for VaR forecasting, a direct financial ML tail-risk forecasting precedent.
- `BuczynskiChlebus2023GARCHNet`: Supports hybrid neural-network/GARCH-style VaR forecasting and the idea of ML-enhanced risk models.
- `KhandaniKimLo2010CreditRiskML`: Verified financial risk-management example using machine-learning algorithms for consumer credit risk.
- `LeoSharmaMaddulety2019MLBankingRisk`: Literature-review support for ML adoption in banking risk management, including interpretability and overfitting concerns.

## Explainable AI in Financial Risk Management

- `BussmannEtAl2020XAIFintechRisk`: Direct XAI-in-fintech-risk-management citation; useful for motivating explainability in regulated financial risk workflows.
- `BarredoArrietaEtAl2020XAI`: General XAI taxonomy and responsible-AI framing; use sparingly for definitions and broad interpretability motivation.
- `RibeiroSinghGuestrin2016LIME`: Local explanation baseline; useful to situate SHAP among model-agnostic explanation approaches.
- `LundbergLee2017SHAP`: Also supports the paper's top-driver explanations when paired with XGBoost artifacts.

## Model Risk Governance and Reproducibility

- `FederalReserveOCC2011SR117ModelRisk`: Federal Reserve SR 11-7 / OCC Bulletin 2011-12 supervisory guidance. Use for the development-validation-governance framing of model risk management. Avoid any claim that DeepFirm Quant is regulator-approved or fully compliant; use "motivated by", "aligned with", or "maps to".
- `Tabassi2023NISTAIRMF`: NIST AI Risk Management Framework 1.0, DOI `10.6028/NIST.AI.100-1`. Use for the Govern, Map, Measure, and Manage functions. Good fit for explaining how artifact contracts, market/data scope, diagnostics, and guardrails form an AI risk-management control surface.
- `IEEEAccessReproducibility2026`: IEEE Access reproducibility author instructions / reproducibility pilot page. Use as an online/manual reference for artifact expectations: code, data or data-access descriptions, dependency requirements, installation/deployment process, benchmarks/tests, documentation, and persistent DOI/versioning where applicable.

## Portfolio Optimization and ML Views

- `Markowitz1952PortfolioSelection`: Mean-variance foundation for portfolio optimization and allocation baselines.
- `BlackLitterman1992GlobalPortfolioOptimization`: Core equilibrium-plus-views Bayesian allocation reference.
- `Meucci2008BlackLittermanExtensions`: Concise extension/reference source for Black-Litterman implementation details.
- `SatchellScowcroft2000BlackLittermanDemystification`: Supports practical interpretation of Black-Litterman as a bridge between quantitative and traditional views.
- `BanElKarouiLim2018MLPortfolioOptimization`: Verified ML/data-driven portfolio optimization source.
- `LiEtAl2022IntelligentBlackLitterman`: Verified Black-Litterman variant using random-forest-based view generation.
- `BaruaSharma2022DynamicBlackLittermanMLViews`: Directly supports Black-Litterman portfolios with views derived from deep-learning predictions.
- `BaruaSharma2023FearGreedMLBlackLitterman`: Directly supports ML-generated relative Black-Litterman views, including XGBoost in the view-construction pipeline.

## Backtest Overfitting, Leakage, and OOS Validation

- `White2000RealityCheck`: Foundational data-snooping test; supports caution around repeated model/strategy search on one historical sample.
- `BaileyEtAl2016BacktestOverfitting`: Direct finance citation for probability of backtest overfitting and combinatorially symmetric cross-validation.
- `BaileyLopezDePrado2014DeflatedSharpe`: Supports correcting Sharpe-ratio claims for selection bias, non-normality, and backtest overfitting.
- `LopezDePrado2018FinancialML`: Practitioner reference for financial ML validation, leakage control, purged/embargoed CV, and avoiding false positives. No DOI found; book metadata verified by ISBN/publisher/library sources.
- `Christoffersen1998IntervalForecasts`: Also useful for OOS evaluation of interval/VaR-style predictions.

## Writing Guidance

- Frame DeepFirm Quant as an auditable decision-support and risk-warning system, not as a claim of superior alpha generation.
- For allocation, cite Black-Litterman sources for Bayesian view fusion and the ML-view papers only when describing the broader literature; make clear the current project uses leakage-guarded, point-in-time signals rather than unconstrained return-prediction backtests.
- For interpretability, avoid claiming SHAP proves causality. Use "driver attribution", "local feature contribution", or "explanation of model output".
- For risk forecasting, distinguish VaR/ES measurement, conditional tail-risk forecasting, and calibrated tail-event classification.
- For model risk governance, say the audit-contract controls are "motivated by" SR 11-7/OCC 2011-12 and "mapped to" NIST AI RMF Govern/Map/Measure/Manage. Do not represent the paper as a legal, regulatory, or full IEEE artifact-review compliance attestation.

## Unverified Citation Entries

- None. All entries in `paper/references.bib` are backed by DOI metadata, official proceedings, publisher pages, ISBN/library records, or official/manual source pages recorded in `paper/citation_verification_log.md`.
