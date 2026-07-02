"""Pipeline layer: orchestrates raw data -> computed metrics.

`compute_metrics.py` wires raw series through the pure `src.metrics`/`src.transformation`
functions into `annual_metrics`/`summary_metrics`. `mock_pipeline.py` exercises that wiring
end to end with hand-written placeholder data; real data sourcing is a later milestone.
"""
