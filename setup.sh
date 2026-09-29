#!/bin/bash
# Preflight checks + environment setup for the pipeline in scr/.
#
# Verifies the venv, installs dependencies, byte-compiles scr/ as a syntax
# check, smoke-tests every third-party import the pipeline needs, and
# validates that INPUT/raw/*.tsv looks like the expected dataset — all
# before touching any data. On success, hands off to scr/main.py.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

INPUT_TSV="INPUT/raw/soc-redditHyperlinks-body.tsv"

echo "================================================"
echo "   Setup   "
echo "   Preflight checks for CC5118 AskReddit's report   "
echo "================================================"

echo
echo "-- Virtual environment --------------------------"

if [[ ! -d "venv" ]]; then
  echo "No venv/ found — creating one with python3 -m venv venv"
  python3 -m venv venv
fi

if [[ ! -f "venv/bin/activate" ]]; then
  echo "Error: activation script not found: venv/bin/activate" >&2
  exit 1
fi

# shellcheck disable=SC1091
source venv/bin/activate

if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  echo "Error: failed to activate the virtual environment" >&2
  exit 1
fi

if [[ ! -x "venv/bin/python3" ]]; then
  echo "Error: Python executable not found in virtual environment: venv/bin/python3" >&2
  exit 1
fi

echo "Installing/checking dependencies from requirements.txt..."
pip install --quiet --disable-pip-version-check -r requirements.txt

echo
echo "-- Compile check (scr/*.py) ---------------------"
python3 -m compileall -q scr
echo "OK: all scr/*.py files compile."

echo
echo "-- Library smoke test ---------------------------"
python3 - <<'PY'
import importlib

modules = ["networkx", "matplotlib", "pandas", "numpy", "scipy", "powerlaw"]
failed = []
for m in modules:
    try:
        importlib.import_module(m)
        print(f"OK: {m}")
    except Exception as e:
        failed.append((m, e))
        print(f"FAIL: {m}: {e}")

if failed:
    raise SystemExit(f"{len(failed)} required librar{'y' if len(failed)==1 else 'ies'} failed to import.")
PY

echo
echo "-- Input dataset validation ----------------------"
if [[ ! -f "$INPUT_TSV" ]]; then
  echo "Error: dataset not found: $INPUT_TSV" >&2
  echo "Download 'soc-redditHyperlinks-body.tsv' from:" >&2
  echo "  https://snap.stanford.edu/data/soc-RedditHyperlinks.html" >&2
  echo "and place it at $INPUT_TSV" >&2
  exit 1
fi

python3 - "$INPUT_TSV" <<'PY'
import sys
sys.path.insert(0, "scr")
from preprocess import validate_input

path = sys.argv[1]
validate_input(path)
print(f"OK: {path} has the expected columns.")
PY

echo
echo "================================================"
echo "   All checks passed.   "
echo "================================================"

MAIN_ARGS=()
CHECK_ONLY=0
for arg in "$@"; do
  if [[ "$arg" == "--check-only" ]]; then
    CHECK_ONLY=1
  else
    MAIN_ARGS+=("$arg")
  fi
done

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  echo "Run 'python3 scr/main.py' to execute the pipeline (or './setup.sh' with no flags to run it now)."
  exit 0
fi

echo
echo "-- Running pipeline (scr/main.py) ----------------"
python3 scr/main.py "${MAIN_ARGS[@]}"
