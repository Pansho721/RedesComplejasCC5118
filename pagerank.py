"""
pagerank.py  —  Ejecutar desde la carpeta raiz del repositorio:
    python pagerank.py

No modifica ningun archivo de Francisco.
Lee el .tsv directamente, genera el grafo negativo y calcula PageRank.
"""

import collections
import csv
import os
import networkx as nx
import pandas as pd

TSV = "soc-redditHyperlinks-body.tsv"

# ── 1. Leer el .tsv y contar arcos por (source, target, sentimiento) ─────────
print("Leyendo el dataset...")
counter = collections.Counter()
with open(TSV, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        src  = row['SOURCE_SUBREDDIT'].strip()
        dst  = row['TARGET_SUBREDDIT'].strip()
        sent = row['LINK_SENTIMENT'].strip()
        counter[(src, dst, sent)] += 1
print(f"  Arcos únicos (source, target, sentimiento): {len(counter)}")

# ── 2. Construir NEG_REDDIT ───────────────────────────────────────────────────
print("Construyendo NEG_REDDIT...")
neg_graph = nx.DiGraph()
for (src, dst, sent), cnt in counter.items():
    if sent == '-1':
        neg_graph.add_edge(src, dst, weight=cnt)
print(f"  Nodos: {neg_graph.number_of_nodes()}, Aristas: {neg_graph.number_of_edges()}")

# ── 3. Calcular PageRank ──────────────────────────────────────────────────────
print("Calculando PageRank...")
pagerank = nx.pagerank(neg_graph, alpha=0.85, weight='weight')

# ── 4. Guardar resultados ─────────────────────────────────────────────────────
os.makedirs("centrality", exist_ok=True)
pr_series = pd.Series(pagerank, name='pagerank').sort_values(ascending=False)
pr_series.index.name = 'node'
pr_series.to_csv("centrality/reddit_negative_pagerank.csv", header=True)
print("  Guardado: centrality/reddit_negative_pagerank.csv")

top10 = pr_series.head(10).reset_index()
top10.columns = ['node', 'pagerank']
top10.to_csv("pagerank_top10.csv", index=False)
print("  Guardado: pagerank_top10.csv")

# ── 5. Imprimir tabla ─────────────────────────────────────────────────────────
print("\n" + "=" * 50)
print("Top 10 subreddits por PageRank en NEG_REDDIT")
print("=" * 50)
print(f"{'#':<4} {'Subreddit':<28} {'PageRank':>10}")
print("-" * 50)
for i, row in top10.iterrows():
    print(f"{i+1:<4} {row['node']:<28} {row['pagerank']:>10.6f}")

# ── 6. Estadísticas para el informe ──────────────────────────────────────────
print("\n" + "=" * 50)
print("Estadísticas útiles para el informe")
print("=" * 50)
print(f"  Máximo : {pr_series.max():.6f}  ({pr_series.idxmax()})")
print(f"  Media  : {pr_series.mean():.6f}")
print(f"  Mediana: {pr_series.median():.6f}")
n_top1 = max(1, int(len(pr_series) * 0.01))
share  = pr_series.head(n_top1).sum() / pr_series.sum() * 100
print(f"  El top 1% de nodos ({n_top1}) acapara el {share:.1f}% del PageRank total")
