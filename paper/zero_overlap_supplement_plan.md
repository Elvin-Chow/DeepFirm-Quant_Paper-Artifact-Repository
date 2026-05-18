# Zero-Security-Overlap Supplement

Status: supplemental crisis-warning run completed on 2026-05-18 HKT without retraining and without sandbox data.

## Purpose

The main holdout set is portfolio-level external validation, but several portfolios share individual securities with the frozen training-domain portfolios. This supplement constructs a stricter holdout set with zero same-market ticker overlap against the frozen `global_h1` and `global_h5` training metadata.

## Training-Domain Source

- Training metadata checked: `artifacts/crisis_warning/global_h1/training_metadata.json`.
- H1 and H5 use the same diversified-global domain definition in the frozen artifacts.
- Frozen artifact directories were not modified.

## Current Main-Holdout Overlap Check

Only one existing main holdout portfolio has zero same-market ticker overlap:

| Market | Existing holdout | Overlap count | Overlapping training tickers |
|---|---|---:|---|
| US | `us_dividend_low_volatility` | 0 | none |

All other existing holdout portfolios share at least one same-market ticker with the frozen training-domain portfolios. The largest overlaps are HK platform/financial core with 5 overlapping tickers, CN new energy healthcare with 4, JP auto/electronics core with 4, and TW electronics supply chain with 4.

## Recommended Zero-Overlap Portfolios

The supplemental portfolio file is `experiments/portfolios/zero_overlap_supplement_portfolios.yaml`. It contains 10 portfolios, two per market, selected from real provider/cache-available tickers and checked to have zero same-market ticker overlap against the frozen training domain.

| Market | Portfolio | Tickers |
|---|---|---|
| US | `us_defensive_income_zero_overlap` | VIG, USMV, KO, PEP, MCD |
| US | `us_midcap_sector_zero_overlap` | MDY, IJR, SMH, XLU, XLI |
| HK | `hk_insurance_industrial_zero_overlap` | 2318.HK, 2020.HK, 1109.HK, 0066.HK, 02822.HK |
| HK | `hk_cross_asset_zero_overlap` | 2318.HK, 2020.HK, 1109.HK, 0066.HK, 03188.HK |
| CN | `cn_consumption_resource_zero_overlap` | 000651, 600887, 002415, 600028, 601088 |
| CN | `cn_state_resource_zero_overlap` | 601857, 600028, 601088, 000651, 600887 |
| JP | `jp_financial_domestic_zero_overlap` | 8316.T, 8766.T, 7011.T, 9433.T, 4452.T |
| JP | `jp_etf_style_zero_overlap` | 1475.T, 1489.T, 2516.T, 8316.T, 9020.T |
| TW | `tw_income_factor_zero_overlap` | 00878.TW, 00919.TW, 2882.TW, 2382.TW, 2891.TW |
| TW | `tw_supply_chain_zero_overlap` | 2357.TW, 2882.TW, 2382.TW, 2891.TW, 00878.TW |

Overlap check result: all 10 recommended portfolios have overlap count 0.

## Config and Commands

Supplement config:

```bash
experiments/zero_overlap_supplement_config.yaml
```

Executed command:

```bash
python experiments/run_crisis_external_eval.py --config experiments/zero_overlap_supplement_config.yaml --output-dir experiments/results_zero_overlap --allow-sandbox-data false
```

Result:

- Portfolio count: 10.
- Prediction rows: 36,114.
- Skipped rows: 0.
- Sandbox data: disabled.
- Output directory: `experiments/results_zero_overlap`.

Threshold-sensitivity command:

```bash
python experiments/run_threshold_sensitivity.py --config experiments/zero_overlap_supplement_config.yaml --results-dir experiments/results_zero_overlap --tables-dir experiments/tables_zero_overlap --figures-dir experiments/figures_zero_overlap --paper-dir paper/zero_overlap_supplement
```

Table/figure command:

```bash
python experiments/make_paper_tables.py --config experiments/zero_overlap_supplement_config.yaml --results-dir experiments/results_zero_overlap --output-dir experiments/tables_zero_overlap --paper-dir paper/zero_overlap_supplement
python experiments/make_paper_figures.py --config experiments/zero_overlap_supplement_config.yaml --results-dir experiments/results_zero_overlap --output-dir experiments/figures_zero_overlap
```

## Supplemental Crisis-Warning Results

| Horizon | Rows | Positives | ROC-AUC | PR-AUC | Brier | Log-loss | Calibration error | Precision@0.60 | Recall@0.60 | Top-decile lift |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| H1 | 18,097 | 934 | 0.6290 | 0.0971 | 0.0480 | 0.2004 | 0.0014 | 0.5000 | 0.0043 | 2.3551 |
| H5 | 18,017 | 1,033 | 0.6139 | 0.0895 | 0.0534 | 0.2192 | 0.0050 | 0.0000 | 0.0000 | 1.8100 |

Threshold highlights:

- Global threshold 0.10: flag rate 3.77%, precision 0.1703, recall 0.1179, F1 0.1394.
- Global threshold 0.60: 8 flags out of 36,114 rows, precision 0.5000, recall 0.0020, F1 0.0041.
- Global top-decile surveillance: precision 0.1138, recall 0.2089, lift 2.0891.
- H5 again has zero flags at 0.60, reinforcing that the fixed threshold is too conservative.

## Suggested Paper Use

Use this as a short supplement or appendix paragraph, not as a replacement for the main holdout results. The zero-overlap run supports the same qualitative conclusion as the main run: modest AUC, weak 0.60 recall, and stronger evidence for ranking/top-decile surveillance than for a fixed binary crisis trigger.

## Remaining Work

- Run baseline comparison on the zero-overlap portfolios if space permits.
- Run allocation OOS on the zero-overlap portfolios only if the paper needs a strict security-disjoint allocation supplement.
- Add zero-overlap result hashes to the final manifest after all supplement files are stable.
