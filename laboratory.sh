#!/bin/bash

echo "================================================"
echo "   Laboratory v0.1   "
echo "   Results used for CC5118 AskReddit's report   "
echo "==============================================="

echo "================================"
echo "   Checking dependencies   "
echo "================================"

INPUT_FILE="soc-redditHyperlinks-body.tsv"
if [[ ! -f "$INPUT_FILE" ]]; then
  echo "Error: file not found: $INPUT_FILE"
  exit 1
fi

if [[ ! -d "venv" ]]; then
  echo "Error: virtual environment directory not found: venv"
  exit 1
fi

if [[ ! -f "venv/bin/activate" ]]; then
  echo "Error: activation script not found: venv/bin/activate"
  exit 1
fi

if [[ ! -x "venv/bin/python3" ]]; then
  echo "Error: Python executable not found in virtual environment: venv/bin/python3"
  exit 1
fi

source venv/bin/activate

if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  echo "Error: failed to activate the virtual environment"
  exit 1
fi
 
pip install -r requirements.txt

echo "================================"
echo "   Preprocess   "
echo "================================"

echo "Starting the preprocessing of the data..."

python3 preprocess.py \
    soc-redditHyperlinks-body.tsv \
    graphs/reddit.edgelist \
    graphs/reddit_weighted.edgelist \
    graphs/reddit_weighted_aggregated.edgelist \
    graphs/reddit_positive.edgelist \
    graphs/reddit_negative.edgelist \
    graphs/reddit_summary.txt

echo "Preprocessing completed."

echo "================================"
echo "   Plotting   "
echo "================================"

echo "Starting the plotting of the graphs..."

g++ Balance_p-way_Vertex-cut.cpp -o PartitionGraph
./PartitionGraph graphs/reddit.edgelist 8

python3 plot.py

echo "Plotting completed."

echo "================================"
echo "   Centrality   "
echo "================================"

python3 centrality.py

echo "Centrality calculations completed."

echo "================================"
echo "   Histograms   "
echo "================================"

python3 histograms.py

echo "Histograms generated successfully."


echo "================================"
echo "   Analysis   "
echo "================================"

python3 analysis.py

echo "Analysis completed."


echo "================================"
echo "   Analysis over Models   "
echo "================================"

python3 models.py

echo "Analysis over Models completed."

echo "================================"
echo "   Laboratory completed successfully   "
echo "================================"