#!/usr/bin/env python3
"""Pipeline orchestrator. This is the only file you should need to edit to
change *what* the pipeline does or *how* it's tuned — every knob lives in
CONFIG below, and every stage is one line in the lazy STAGES list.

Usage:
    python3 scr/main.py [--verbose] [--only stage1,stage2,...]

Stages: preprocess, centrality, histogram, analysis, models, report
"""
import argparse
import os
import sys
import time

# Let the stage modules import each other by plain name (e.g. `import
# palette`) regardless of the working directory this is launched from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import preprocess
import centrality as centrality_stage
import histogram as histogram_stage
import analysis as analysis_stage
import models as models_stage
import report as report_stage

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# CONFIG — every tunable knob for the pipeline lives here. Edit this dict (or
# override individual keys before calling run_pipeline) to change paths,
# which centrality measures run per graph, or model-parameter overrides.
# ---------------------------------------------------------------------------
CONFIG = {
    "verbose": False,
    "paths": {
        "input_tsv": os.path.join(REPO_ROOT, "INPUT", "raw", "soc-redditHyperlinks-body.tsv"),
        "edgelist_dir": os.path.join(REPO_ROOT, "INPUT", "edgelist"),
        "output_raw": os.path.join(REPO_ROOT, "OUTPUT", "raw"),
        "output_pages": os.path.join(REPO_ROOT, "OUTPUT", "pages", "final"),
    },
    # Which centrality measures to compute for each named graph. Trimming
    # this list is the main lever for runtime: betweenness/closeness on
    # CONX_REDDIT dominate the pipeline's wall-clock time.
    "centrality_kinds": {
        "AGG_REDDIT": ["degree", "pagerank"],
        "CONX_REDDIT": ["degree", "betweenness", "closeness", "alpha-centrality", "pagerank"],
        "NEG_REDDIT": ["degree", "in-degree", "out-degree", "alpha-centrality", "pagerank"],
    },
    # Force a specific synthetic-model parameter instead of estimating it
    # from the data (see models.estimate_params) — e.g. {"m": 4}.
    "model_params_override": {},
}

# ---------------------------------------------------------------------------
# Lazy pipeline: each stage is (name, callable, kwargs-fn). Comment a line
# out, reorder, or point `only` at a subset to change what runs — nothing
# else in this file, or in the stage modules, needs to change.
# ---------------------------------------------------------------------------
STAGES = [
    ("preprocess", preprocess.run),
    ("centrality", centrality_stage.run),
    ("histogram", histogram_stage.run),
    ("analysis", analysis_stage.run),
    ("models", models_stage.run),
    ("report", report_stage.run),
]


def run_pipeline(config=CONFIG, only=None):
    results = {}
    for name, func in STAGES:
        if only and name not in only:
            continue
        print(f"\n{'=' * 60}\n  Stage: {name}\n{'=' * 60}")
        t0 = time.time()
        results[name] = func(config)
        print(f"  -> {name} done in {time.time() - t0:.1f}s")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="show detailed per-stage progress")
    parser.add_argument("--only", help="comma-separated stage names to run, e.g. --only histogram,report")
    args = parser.parse_args()

    CONFIG["verbose"] = args.verbose
    only = set(args.only.split(",")) if args.only else None

    run_pipeline(CONFIG, only=only)


if __name__ == "__main__":
    main()
