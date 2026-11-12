# Reproducibility

This file holds the reproducibility record that accompanied the manuscript as
Appendix A up to v1. It is kept in the repository so the article does not carry
file paths that only make sense next to the code.

## Software environment

All stages run under Python 3.12 on a single workstation. Package versions are
pinned in two files: `code/requirements.txt` covers Stages II-IV and the
reporting scripts, and `code/gis/requirements-gis.txt` covers the Stage I raster
and vector processing, which needs a separate geospatial stack.

- Optimisation: Pyomo 6.10.1 calling HiGHS through `highspy` 1.15.1
- Geospatial: GeoPandas 1.2.0, Shapely 2.2.0, pyproj 3.8.0, rasterio 1.5.2, pyogrio 0.13.0
- Numerical and reporting: NumPy 2.1.1, pandas 2.2.2, SciPy 1.14.1, scikit-learn 1.8.0, Matplotlib 3.9.2
- Wind profiles: windpowerlib 0.2.2

## Scripts by stage

Rows are in execution order: later steps consume the outputs written by earlier
ones, so running them out of order fails on missing inputs rather than producing
wrong numbers. Paths are relative to the repository root.

| Step | Script |
|---|---|
| Stage I screening and candidate selection | `code/gis/gis_pipeline_real.py` |
| Stage I threshold sensitivity | `code/gis/sensitivity_stageB.py` |
| Road distances between network nodes | `code/network/distance_matrix.py` |
| Hourly wind and PV profiles | `code/optimization/profiles.py` |
| Stage II data-derived criteria K1-K4 | `code/mcdm/stage2_data_criteria.py` |
| Stage II spherical fuzzy CRITIC-WASPAS ranking | `code/mcdm/sf_critic_waspas.py` |
| Stage II leave-one-expert-out test | `code/mcdm/leave_one_expert_out.py` |
| Stage III network model | `code/optimization/rpp_model.py` |
| Stage III scenario, Pareto and outage runs | `code/optimization/run_stage3_batch.py` |
| Stage IV Monte Carlo evaluation | `code/optimization/stage4_monte_carlo.py` |
| Emission accounting and RFNBO check | `code/optimization/emissions.py` |
| Result aggregation | `code/optimization/summarise_stage3.py` |
| Numbers reported in the text and tables, written to a single JSON file | `code/optimization/manuscript_numbers.py` |
| Method overview figure | `code/tools/make_method_figure.py` |
| Reproduction check | `code/tools/verify_reproduction.py` |

## Supplementary tables as data files

The supplementary document is typeset from five machine-readable CSV files under
`submission_assets/supplementary/`, which can be read without parsing the PDF.
The caption and source-note files in the same directory, and the script
`code/tools/make_supplementary.py` that assembles them into the supplementary
document, are also in the repository.

| Supplementary table | Data file |
|---|---|
| S1a-S1c Demand node inventory | `Supplementary_Table_S1_Demand_Inventory.csv` |
| S2 Stage III techno-economic parameters | `Supplementary_Table_S2_Parameter_Sources.csv` |
| S3a Coded siting studies | `Supplementary_Table_S3_Coded_Studies.csv` |
| S3b Criterion-by-study matrix | `Supplementary_Table_S3_Criterion_Frequency.csv` |
| S4a-S4c Stage I screening detail | `Supplementary_Table_S4_Notes.txt` |

## Scope of the reproduction check

The check reported in the Conclusion covers Stage I selection, the Stage II
scores and the baseline Stage III solution, each regenerated from the frozen
inputs in a clean environment built from the pinned requirement files. The
remaining Stage III scenarios, the Pareto front and the Monte Carlo runs use the
same scripts but were not re-run in a clean environment. Mixed-integer solutions
may differ slightly across solver versions and hardware within the stated 0.1 %
optimality gap, so exact objective values are not guaranteed to be bit-identical
on a different machine.
