import matplotlib.pyplot as plt
import pandas as pd
import os

# ==========================================================================================
#               Histogram construction
# ==========================================================================================

neg_centrality = pd.read_csv("centrality/reddit_negative_centrality_degree.csv", sep='\t', names=['node', 'degree'])

print("Constructing degree distribution dot diagram for negative graph...")
degrees = neg_centrality['degree']
counts = degrees.value_counts().sort_index()
total = counts.sum()
plt.figure()
plt.scatter(counts.index, counts.values / total, s=3, color='black')
plt.xscale('log')
plt.yscale('log')
plt.title("NEG_REDDIT | Distribución de frecuencia: Degree")
plt.xlabel("Degree")
plt.ylabel("Frecuencia")
os.makedirs("histograms", exist_ok=True)
plt.savefig("histograms/reddit_negative_degree_histogram.png")