# Figure Captions

These captions are drafted for the Markdown-to-IEEE conversion. All paper numbers use real-data outputs with sandbox data disabled.

## Figure 1. Framework Architecture

Auditable DeepFirm Quant workflow from real-market data ingestion through frozen H1/H5 crisis-warning artifacts, SHAP-style explanation, leakage-guarded allocation, and paper outputs. The figure summarizes the audit contract used in the experiments: artifact hash validation, schema-hash validation, provenance logging, data-availability skips instead of sandbox substitution, and policy-as-of checks.

Source: `experiments/figures/framework_architecture.png`.

## Figure 2. ROC and Precision-Recall by Horizon

ROC and precision-recall curves for 68,324 real-data holdout crisis predictions with sandbox disabled. The rows cover 34,238 H1 predictions and 34,086 H5 predictions after skipping `cn_broad_factor_etf` for both horizons because real provider data for `159915` was unavailable. The precision-recall panel is more informative than ROC for rare tail events because the positive event rate is about 5.5%.

Source: `experiments/figures/roc_pr_by_horizon.png`.

## Figure 3. Calibration by Horizon

Calibration curves for the same real-data H1/H5 holdout predictions used in Figure 2, with sandbox disabled and the same skipped portfolio policy. The figure evaluates probability quality, not the operational threshold. Threshold selection is analyzed separately in Table 6 and Figure 4.

Source: `experiments/figures/calibration_by_horizon.png`.

## Figure 4. Threshold Sensitivity

Precision, recall, F1, and flag rate across thresholds 0.05, 0.075, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, and 0.60 for real-data holdout predictions with sandbox disabled. The 0.60 threshold is marked as conservative: it flags 11 H1 rows and zero H5 rows. Lower thresholds recover recall only by increasing flag volume, so the evidence better supports ranking surveillance than a fixed binary crisis trigger.

Source: `experiments/figures/threshold_sensitivity.png`.

## Figure 5. SHAP-Style Warning Drivers

Mean absolute native XGBoost contribution values for recent holdout warning rows across H1 and H5 artifacts. The figure uses SHAP-style contribution output from frozen artifacts on real-data holdout rows with sandbox disabled. The drivers support audit review and user communication, but they are not causal market stress-test variables.

Source: `experiments/figures/shap_top_drivers.png`.

## Figure 6. Allocation OOS Curves

Mean OOS cumulative log-return curves for allocation strategies across 19 evaluated real-data holdout portfolios, 114 strategy rows, and 42,420 return rows with sandbox disabled. `cn_broad_factor_etf` was skipped because real provider data for `159915` was unavailable. The figure should be read with Table 4 because all strategies have negative mean benchmark excess return.

Source: `experiments/figures/allocation_oos_curves.png`.

## Figure 7. Allocation Strategy Ablation

Coarse strategy-level allocation ablation over the same 19 real-data OOS portfolios used in Figure 6. Deltas are relative to Smart policy with OOS guard where present. The figure is not a component-level causal ablation of each Smart-policy signal.

Source: `experiments/figures/ablation_summary.png`.
