# Testing & iteration guide

Handoff notes for whoever (human or assistant) picks this up next. Read
`CLAUDE.md` first for the architecture; this file is only about **how to
safely verify changes** on this specific machine.

## The one constraint that matters: RAM

This machine has **8GB RAM** (7.1GB usable) and a small swap file. It runs
low on free memory even at idle (VSCode + extensions alone can eat 3-4GB).
Two stages fork/spawn worker processes over large graphs and can push the
machine into heavy swapping or kill the process silently:

- `centrality.py` → `betweenness_centrality_parallel()` (`multiprocessing.Pool`)
  on `CONX_REDDIT` (~11.5k nodes, ~98k edges).
- `models.py` → `compare_models()` (`ProcessPoolExecutor`, 4 workers) building
  and analyzing 5 graphs per comparison, twice (AGG + CONX).

**Never run the full `python3 scr/main.py` unattended as a "let's just see if
it works" check.** Before running it for real, run `free -h` — if "available"
is under ~3GB, close other apps or expect swapping. If you only need to
verify *logic* changes, use the tiered approach below instead; it never
touches the real ~11k-node graph.

Check for stray background processes with (plain `pgrep -f "main.py"` will
match its own argv and lie to you):

```bash
for pid in $(pgrep -f python3); do
  cmd=$(tr '\0' ' ' < /proc/$pid/cmdline 2>/dev/null)
  case "$cmd" in *scr/main.py*|*ProcessPoolExecutor*) echo "PID $pid: $cmd" ;; esac
done
```

To kill a runaway run: `kill -TERM <pid>` (it owns a process pool; `pkill -P
<pid>` first to catch children if TERM alone doesn't clean them up).

## Tiered validation strategy

Go top-down. Stop as soon as you've validated what you changed — you don't
need tier 4 to check a report.py CSS tweak.

### Tier 1 — syntax / imports (seconds, no data)

```bash
python3 -m compileall -q scr
python3 -c "import sys; sys.path.insert(0,'scr'); import preprocess, centrality, histogram, analysis, models, report, palette, graph_io"
```

Or just `./setup.sh --check-only`, which does this plus the library smoke
test and TSV header validation.

### Tier 2 — synthetic tiny graphs (seconds, trivial memory)

Validates algorithmic correctness of anything you touched in
`centrality.py`/`analysis.py`/`models.py` without loading real data. Pattern:
build a `nx.gnp_random_graph` with 20-60 nodes, call the function, compare
against the plain NetworkX equivalent where one exists.

```bash
source venv/bin/activate
python3 - <<'PY'
import sys; sys.path.insert(0, "scr")
import networkx as nx, centrality

G = nx.DiGraph(nx.gnp_random_graph(60, 0.08, seed=1, directed=True))
expected = nx.betweenness_centrality(G)
got = centrality.betweenness_centrality_parallel(G, processes=2)
diff = max(abs(expected[n] - got[n]) for n in G.nodes())
assert diff < 1e-9, diff
print("OK, diff =", diff)
PY
```

Do the same for `models.small_world_analysis` / `properties_analysis` against
each `MODEL_BUILDERS` entry with small `N` (30-50), and for
`analysis.small_world_stats` / `assortativity_stats` / `bowtie` and their
`plot_*` companions — all cheap, all single-process except the
`ProcessPoolExecutor` calls in `models.compare_models`, which are still fine
at N≈40.

This tier already caught nothing wrong last round — `betweenness_centrality_parallel`
matched `nx.betweenness_centrality` to 1e-17, and every chart function ran
clean — so it's a solid bar before touching real data.

### Tier 3 — real data, cheap stages only (seconds to ~1 min)

Safe to run against the real dataset because they're single-process and
operate on already-small inputs (CSVs, or graphs under a few tens of
thousands of nodes with no expensive all-pairs algorithm):

```bash
source venv/bin/activate
python3 - <<'PY'
import sys; sys.path.insert(0, "scr")
from main import CONFIG
import preprocess, histogram, report

preprocess.run(CONFIG)   # ~12s, just text parsing
histogram.run(CONFIG)    # reads existing centrality CSVs, builds plots + power-law fit
report.run(CONFIG)       # reads OUTPUT/raw only — see note below
PY
```

`centrality.run(CONFIG)` is also fine here **as long as you don't ask for
betweenness/closeness on CONX_REDDIT** — degree, in/out-degree,
alpha-centrality, and pagerank on AGG_REDDIT/NEG_REDDIT/CONX_REDDIT are all
cheap single-pass computations. To test just those, temporarily edit
`CONFIG["centrality_kinds"]` in a scratch script (don't commit the edit) to
drop `"betweenness"` and `"closeness"`.

**`report.run(CONFIG)` is always safe and always cheap** — it only reads
files under `OUTPUT/raw/`, never loads a graph or recomputes anything (see
"reads only from OUTPUT/raw" in CLAUDE.md). Re-run it after any change to
`report.py`, even with partial `OUTPUT/raw` content (missing CSVs render as
an explicit "sin datos" message per page, not a crash) — that's the fastest
iteration loop for template/CSS/copy changes:

```bash
python3 -c "import sys; sys.path.insert(0,'scr'); from main import CONFIG; import report; report.run(CONFIG)"
# then open OUTPUT/pages/final/main.html (or any *.html) in a browser
```

After editing, spot-check with:
```bash
grep -o '<img[^>]*>' OUTPUT/pages/final/*.html   # every src should resolve under OUTPUT/pages/final/img/
```

### Tier 4 — the real, expensive run (only when you mean it)

```bash
free -h                          # confirm you actually have headroom
source venv/bin/activate
python3 scr/main.py --verbose --only centrality,models 2>&1 | tee /tmp/run.log &
disown
# then poll safely:
watch -n 10 'free -h; tail -5 /tmp/run.log'
```

`--only` lets you isolate just the stage(s) you changed instead of
re-running everything. If you only touched `analysis.py`, run `--only
analysis` — it still loads AGG/NEG/POS and computes
`average_shortest_path_length`/`average_clustering` on `CONX_REDDIT`
(single-process, no fork storm, but still O(V·E) ≈ 10^9 ops — expect minutes,
not seconds).

If it dies (silently, from OOM) or you need to interrupt it, use the
per-PID `/proc/cmdline` check above before assuming it's gone — a plain
`pgrep -af "scr/main.py"` will self-match the very shell command you type to
check.

## What's already validated (as of the scr/ refactor)

- Tier 1: clean.
- Tier 2: `betweenness_centrality_parallel` exact-matched against
  `nx.betweenness_centrality`; `models.py` dispatch + `ProcessPoolExecutor`
  wiring on synthetic N=40 graphs; every `plot_*` function in
  `analysis.py`/`models.py` on synthetic graphs.
- Tier 3: `preprocess.run` on the real TSV (full, correct); `centrality.run`
  for `NEG_REDDIT`/`AGG_REDDIT` on real data with all their configured kinds
  (degree, in/out-degree, alpha-centrality, pagerank — no betweenness needed
  for those two); `histogram.run` on the real partial output;
  `report.run` on real partial `OUTPUT/raw` — all HTML pages render, all
  image paths resolve, missing-data fallbacks work.
- **Not yet run at real scale**: `centrality.py`'s betweenness/closeness for
  `CONX_REDDIT`, and `models.compare_models` against the real AGG/CONX
  graphs (Tier 4). Both are thin wrappers around Tier-2-validated logic, but
  haven't seen the real ~11.5k-node graph. Do this on a machine with more
  headroom, or free up RAM here first (close VSCode extensions / browser,
  check `free -h` shows >4GB available) before running `--only
  centrality,models`.

## Quick reference: what needs re-running after touching what

| You changed... | Re-run |
|---|---|
| `preprocess.py` | `--only preprocess` (fast), then whatever downstream stage you're checking |
| `centrality.py` logic | Tier 2 synthetic check first; Tier 3 for non-CONX kinds; Tier 4 for betweenness/closeness |
| `histogram.py` | Tier 3 (`histogram.run`) — reads existing centrality CSVs, no graph loading |
| `analysis.py` | Tier 2 synthetic check first; Tier 4 for the real small-world numbers (loads CONX_REDDIT) |
| `models.py` | Tier 2 synthetic check first; Tier 4 for the real comparison |
| `report.py` / `palette.py` (HTML, CSS, colors, copy) | Tier 3 (`report.run`) only — never needs the graphs |
| `setup.sh` | `./setup.sh --check-only` |
