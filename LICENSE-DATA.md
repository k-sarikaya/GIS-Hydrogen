# Data licence

The **code** in this repository is released under the MIT Licence (see `LICENSE`).

The **data files** produced by this study — everything under `data/processed/`,
the parameter set, and the supplementary tables distributed as CSV — are
released under the
[Creative Commons Attribution 4.0 International licence (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

You are free to share and adapt them for any purpose, including commercially,
provided you give appropriate credit to the source publication.

## Third-party inputs

Files under `data/raw/` are redistributed snapshots of third-party open
datasets, kept so that the screening step is exactly reproducible. They remain
under the licence of their original provider, which the entry for each dataset
in Supplementary Table S8 identifies. Among them:

| Source | Licence |
|---|---|
| OpenStreetMap extracts | Open Database Licence (ODbL) 1.0, © OpenStreetMap contributors |
| geoBoundaries | CC BY 4.0 |
| Copernicus DEM (GLO-90) | Copernicus / ESA licence terms |
| ESA WorldCover | CC BY 4.0 |
| Global Wind Atlas | CC BY 4.0 |
| PVGIS (SARAH3) | European Commission reuse terms |
| ERA5 reanalysis | Copernicus Climate Change Service licence |
| Natural Earth | Public domain |

Where a provider's terms are more restrictive than CC BY 4.0, the provider's
terms govern that file.

## Data not included

Individual expert survey responses are **not** included in this repository.
They are personal data collected under an informed-consent form that limits
their use to this study, and the panel is small enough that responses would be
re-identifiable. The aggregated spherical-fuzzy values actually used by the
model are provided in `data/processed/stage2/aggregated_expert_sfn.csv`, and
the survey instrument, invitation text and consent form are in `survey/`, so
the elicitation can be inspected and repeated.
