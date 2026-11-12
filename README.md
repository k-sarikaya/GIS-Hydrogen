# Green hydrogen supply chain design for Türkiye

Code, frozen open-data inputs and processed results for:

> Sarıkaya, K. *From Land Eligibility to Pipeline Corridors: An Integrated
> GIS–Spherical-Fuzzy–Robust-Possibilistic Design of Türkiye's Green Hydrogen
> Supply Chain.* Submitted to the International Journal of Hydrogen Energy.

The study asks whether expert-informed siting preferences and possibilistic
hedging change a national green hydrogen network when land and logistics
constrain it, and tests each layer against a counterfactual rather than
assuming it matters.

## Framework

| Stage | What it does | Entry point |
|---|---|---|
| I | Pixel-level GIS screening of eligible land at ~90 m resolution, then clustering into candidate sites | `code/gis/gis_pipeline_real.py` |
| II | Spherical-fuzzy CRITIC–WASPAS ranking of the candidates, separating measured criteria from expert judgement | `code/mcdm/sf_critic_waspas.py` |
| III | Seasonal robust possibilistic MILP for production, pipelines, trailers and cavern storage | `code/optimization/rpp_model.py` |
| IV | Monte Carlo evaluation on the same coefficients, plus RFNBO emissions accounting | `code/optimization/stage4_monte_carlo.py` |

## Installation

```bash
pip install -r code/requirements.txt
pip install -r code/gis/requirements-gis.txt   # Stage I only
```

Stage III solves MILPs through Pyomo with the HiGHS solver.

## Running the pipeline

All commands are run from the repository root.

```bash
# Stage I — full run (~15 min, needs network access)
python code/gis/gis_pipeline_real.py --out data/raw/gis/real

# Stage I — selection step only (deterministic, no network), and threshold sensitivity
python code/gis/gis_pipeline_real.py --from-features data/raw/gis/real/grid_cells_features.csv --out <dir>
python code/gis/sensitivity_stageB.py

# Candidate x demand road distance matrix (OSRM response is frozen; --refresh re-queries)
python code/network/distance_matrix.py --sites data/raw/gis/real/candidate_sites.csv --rule rule_2040

# Stage II — ranking and its robustness checks
python code/mcdm/sf_critic_waspas.py
python code/mcdm/leave_one_criterion_out.py
python code/mcdm/leave_one_expert_out.py
python code/mcdm/method_comparison.py
python code/mcdm/alpha_sweep_table.py          # weight-blend sensitivity (Supplementary Table S13)

# Stage III — baseline, sensitivity runs and the Pareto front
python code/optimization/run_stage3_batch.py
python code/optimization/rpp_model.py --scenario base --tag base_pareto --set rpp.pareto_points=5

# Stage IV — Monte Carlo, emissions, summaries
python code/optimization/stage4_monte_carlo.py
python code/optimization/emissions.py
python code/optimization/summarise_stage3.py
python code/optimization/manuscript_numbers.py   # single source of the derived numbers in the paper

# Checks
python code/tools/verify_reproduction.py         # clean-environment reproduction check
python code/tools/check_manuscript_numbers.py    # every table/figure number against its run
python code/tools/check_citations.py
python code/tools/verify_references.py           # bibliography against Crossref / DataCite

# Manuscript
cd manuscript && latexmk -pdf manuscript.tex
```

## Reproducibility

- **Stage I runs in two steps.** The *extract* step processes every source in
  memory and freezes a cell-level feature table, the OpenStreetMap snapshots,
  and the URL plus SHA-256 checksum of each input together with package
  versions (`features_manifest.json`). The *select* step is deterministic and
  reads only that table, so the threshold sensitivity analysis repeats exactly
  without network access. Output checksums are written to `gis_summary.json`.
- **Pinned versions.** Stage I packages are in `code/gis/requirements-gis.txt`,
  the remaining stages in `code/requirements.txt`.
- **Clean-environment check (30 October 2026).** In a virtual environment built
  from scratch, `code/tools/verify_reproduction.py` reproduced the Stage I
  selection checksums exactly, Stage II `Q01` to within 5e-7 with an identical
  ranking, and the baseline Stage III objective exactly. The other Stage III
  scenarios, the Pareto front and the Monte Carlo were produced with the same
  scripts but not re-run in the clean environment; MILP solutions may differ
  within the 0.1% gap depending on solver version and hardware.
- **Frozen responses.** The PVGIS and tile caches (`cache_*.csv`) and the OSRM
  routing response (`osrm_response.json`) are stored rather than re-queried.

`docs/REPRODUCIBILITY.md` gives the software environment and the stage-to-script
mapping in full.

## Data

Included: the parameter set with its sources and evidence levels, the frozen
open-data inputs, all processed results behind the tables and figures, the
supplementary tables as machine-readable CSV, and the survey instrument.

Not included: individual expert survey responses. They are personal data
collected under an informed-consent form, and with four respondents they would
be re-identifiable. The aggregated spherical-fuzzy values the model actually
uses are in `data/processed/stage2/aggregated_expert_sfn.csv`; the questionnaire,
invitation text and consent form are in `survey/`, so the elicitation can be
inspected and repeated. `data/survey/expert_responses_SYNTHETIC.csv` exists for
code testing only and must not be used for analysis.

Two further notes on scope, also stated in the paper's limitations: no
basin-level water abstraction quota is imposed in Stage III, because no verified
open spatial dataset was available for the candidate basins (water stress enters
through the Stage II ranking instead, at a nominal 17.5 L/kg set in
`params.yaml`); and the outage scenarios test full-year loss of the cavern or of
the most heavily used pipeline, not partial or 30-day outages.

## Licence

Code is released under the MIT Licence (`LICENSE`). Data produced by this study
are released under CC BY 4.0. Redistributed third-party inputs under
`data/raw/` remain under their providers' licences. See `LICENSE-DATA.md`.

## Contact

Kadir Sarıkaya — Department of Industrial Engineering, Tokat Gaziosmanpaşa
University, Tokat, Türkiye — kadir.sarikaya@gop.edu.tr
