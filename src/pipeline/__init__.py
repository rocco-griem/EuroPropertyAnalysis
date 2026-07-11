"""Pipeline layer: orchestrates raw data -> computed metrics.

`compute_metrics.py` wires raw series through the pure `src.metrics`/`src.transformation`
functions into `annual_metrics`/`summary_metrics`. `csv_loader.py` reads the committed CSVs in
`data/raw/`; `real_pipeline.py` loads them into the database and runs `compute_metrics` for
every capital in `settings.CAPITALS`.
"""
