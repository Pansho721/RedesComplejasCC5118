#!/bin/bash

echo "================================"
echo "Laboratory"
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