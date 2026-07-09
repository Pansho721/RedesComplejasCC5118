#!/bin/bash

echo "================================================"
echo "   Laboratory v0.1   "
echo "   Results used for CC5118 AskReddit's report   "

echo "==============================================="

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

g++ Balanced_p-way_Vertex-cut.cpp -o PartitionGraph
./PartitionGraph graphs/reddit.edgelist 8

python3 plot.py

echo "Plotting completed."

