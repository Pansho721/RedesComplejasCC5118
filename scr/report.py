"""Stage: build the HTML report.

Deliberately reads OUTPUT/raw (CSVs + PNGs already written by the earlier
stages) as its only data source, rather than the in-memory return values of
preprocess/centrality/histogram/analysis/models. That means the report can
be regenerated on its own - `python3 -c "from main import ...; report.run(CONFIG)"`
- any time OUTPUT/raw exists, without recomputing centrality or re-running
the model comparisons.

One HTML page answers one question (centrality, degree distribution,
small-world, assortativity, bow-tie, models), plus a main.html summary
linking all of them. Every image a page references is copied into
OUTPUT/pages/final/img/ with a flattened, de-duplicated filename, so the
whole OUTPUT/pages/final/ directory is self-contained and can be moved or
zipped as one unit.
"""
import csv
import html
import os
import shutil
from datetime import datetime

import palette

NAV = [
    ("main", "Resumen", "main.html"),
    ("centrality", "Centralidad", "centrality.html"),
    ("degree_distribution", "Distribución de grado", "degree_distribution.html"),
    ("small_world", "Mundo pequeño", "small_world.html"),
    ("assortativity", "Asortatividad", "assortativity.html"),
    ("bowtie", "Bow-tie", "bowtie.html"),
    ("models", "Modelos sintéticos", "models.html"),
]

CSS = f"""
:root {{
  color-scheme: light;
  --surface: {palette.SURFACE};
  --page: {palette.PAGE};
  --ink: {palette.INK};
  --ink-2: {palette.INK_SECONDARY};
  --muted: {palette.MUTED};
  --grid: {palette.GRID};
  --axis: {palette.AXIS};
  --border: {palette.BORDER};
  --accent: {palette.BLUE};
  padding-top: env(safe-area-inset-top, 0px);
  padding-bottom: env(safe-area-inset-bottom, 0px);
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    color-scheme: dark;
    --surface: #1a1a19;
    --page: #0d0d0d;
    --ink: #ffffff;
    --ink-2: #c3c2b7;
    --muted: #898781;
    --grid: #2c2c2a;
    --axis: #383835;
    --border: rgba(255,255,255,0.10);
    --accent: #3987e5;
  }}
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--page);
  color: var(--ink);
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  font-size: 15px;
  line-height: 1.55;
}}
img {{ max-width: 100%; }}
[hidden] {{ display: none !important; }}
header.top {{
  position: sticky;
  top: env(safe-area-inset-top, 0px);
  z-index: 10;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0 20px;
}}
nav {{
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  max-width: 1040px;
  margin: 0 auto;
  padding: 10px 0;
}}
nav a {{
  color: var(--ink-2);
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  padding: 6px 10px;
  border-radius: 6px;
}}
nav a:hover {{ background: var(--grid); color: var(--ink); }}
nav a.active {{ color: var(--accent); background: color-mix(in srgb, var(--accent) 14%, transparent); }}
main {{
  max-width: 1040px;
  margin: 0 auto;
  padding: 28px 20px 60px;
}}
h1 {{ font-size: 26px; margin: 4px 0 6px; }}
h2 {{ font-size: 18px; margin: 36px 0 12px; }}
p.lede {{
  color: var(--ink-2);
  font-size: 14px;
  margin: 0 0 20px;
}}
.answer {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 4px solid var(--accent);
  border-radius: 8px;
  padding: 14px 18px;
  margin: 0 0 28px;
  font-size: 14.5px;
}}
.answer strong {{ color: var(--ink); }}
.tiles {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin: 0 0 8px;
}}
.tile {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
}}
.tile .label {{
  color: var(--muted);
  font-size: 11.5px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}}
.tile .value {{
  font-size: 22px;
  font-weight: 700;
  margin-top: 4px;
  font-variant-numeric: proportional-nums;
}}
.cards {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 14px;
  margin: 8px 0 8px;
}}
a.card {{
  display: block;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px 18px;
  text-decoration: none;
  color: var(--ink);
}}
a.card:hover {{ border-color: var(--accent); }}
a.card .q {{ font-weight: 700; font-size: 14.5px; }}
a.card .a {{ color: var(--ink-2); font-size: 13px; margin-top: 6px; }}
.chart-card {{
  background: #fcfcfb;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px;
  margin: 6px 0 22px;
}}
.chart-card figcaption {{
  color: var(--muted);
  font-size: 12.5px;
  margin-top: 8px;
  text-align: center;
}}
.chart-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}}
.table-wrap {{ overflow-x: auto; margin: 0 0 24px; }}
table {{
  border-collapse: collapse;
  width: 100%;
  font-size: 13.5px;
}}
th, td {{
  text-align: left;
  padding: 7px 10px;
  border-bottom: 1px solid var(--grid);
  white-space: nowrap;
}}
th {{ color: var(--muted); font-weight: 600; font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.03em; }}
td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
footer {{
  max-width: 1040px;
  margin: 20px auto 0;
  padding: 16px 20px 40px;
  color: var(--muted);
  font-size: 12px;
}}
"""


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def _e(value):
    return html.escape(str(value))


def _fmt(value, nd=4):
    try:
        return f"{float(value):.{nd}f}"
    except (TypeError, ValueError):
        return _e(value)


def _read_csv(path):
    if not os.path.isfile(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _table(headers, rows, numeric_cols=()):
    if not rows:
        return "<p class=\"lede\">Sin datos disponibles.</p>"
    thead = "".join(f'<th class="{"num" if h in numeric_cols else ""}">{_e(h)}</th>' for h in headers)
    body_rows = []
    for row in rows:
        cells = []
        for h in headers:
            v = row.get(h, "")
            v = _fmt(v) if h in numeric_cols else _e(v)
            cls = ' class="num"' if h in numeric_cols else ""
            cells.append(f"<td{cls}>{v}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")
    return f'<div class="table-wrap"><table><thead><tr>{thead}</tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>'


def _tiles(items):
    tiles = "".join(
        f'<div class="tile"><div class="label">{_e(label)}</div><div class="value">{_e(value)}</div></div>'
        for label, value in items
    )
    return f'<div class="tiles">{tiles}</div>'


class AssetCopier:
    """Copies chart PNGs referenced by the report into OUTPUT/pages/final/img,
    de-duplicating filenames so the final page directory is self-contained
    and movable as a single unit."""

    def __init__(self, img_dir):
        self.img_dir = img_dir
        self._used = {}
        os.makedirs(img_dir, exist_ok=True)

    def copy(self, src_path):
        if not src_path or not os.path.isfile(src_path):
            return None
        base = os.path.basename(src_path)
        name, ext = os.path.splitext(base)
        n = self._used.get(base, 0)
        self._used[base] = n + 1
        dest_name = base if n == 0 else f"{name}_{n}{ext}"
        shutil.copy2(src_path, os.path.join(self.img_dir, dest_name))
        return f"img/{dest_name}"


def _figure(assets, src_path, caption):
    rel = assets.copy(src_path)
    if not rel:
        return f'<p class="lede">(figura no disponible: {_e(src_path)})</p>'
    return f'<figure class="chart-card"><img src="{rel}" alt="{_e(caption)}"><figcaption>{_e(caption)}</figcaption></figure>'


def _page(active, title, question, answer_html, body_html):
    nav_html = "".join(
        f'<a href="{href}" class="{"active" if key == active else ""}">{_e(label)}</a>'
        for key, label, href in NAV
    )
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{_e(title)}</title>
<style>{CSS}</style>
</head>
<body>
<header class="top"><nav>{nav_html}</nav></header>
<main>
<h1>{_e(question)}</h1>
<div class="answer">{answer_html}</div>
{body_html}
</main>
<footer>CC5118 · Redes Complejas · Reddit Hyperlinks — generado el {datetime.now().strftime('%Y-%m-%d %H:%M')}</footer>
</body>
</html>"""


# ---------------------------------------------------------------------------
# per-question page builders — each reads only from OUTPUT/raw
# ---------------------------------------------------------------------------

GRAPH_ORDER = ["AGG_REDDIT", "CONX_REDDIT", "NEG_REDDIT"]


def _find_graphs(summary_dir):
    found = []
    if os.path.isdir(summary_dir):
        for fn in sorted(os.listdir(summary_dir)):
            if fn.startswith("reddit_") and fn.endswith("_centrality_full_centrality.csv"):
                found.append(fn[len("reddit_"): -len("_centrality_full_centrality.csv")])
    return [g for g in GRAPH_ORDER if g in found] + [g for g in found if g not in GRAPH_ORDER]


def build_centrality_page(raw_dir, assets):
    centrality_dir = os.path.join(raw_dir, "centralities")
    summary_dir = os.path.join(centrality_dir, "summary")
    images_dir = os.path.join(raw_dir, "images")

    graphs = _find_graphs(summary_dir)
    sections = []
    top_overall = None

    for g in graphs:
        csv_path = os.path.join(summary_dir, f"reddit_{g}_centrality_full_centrality.csv")
        rows = _read_csv(csv_path)
        if not rows:
            continue
        headers = list(rows[0].keys())
        numeric = [h for h in headers if h != "node"]
        top10 = rows[:10]
        if top_overall is None and top10:
            top_overall = (g, top10[0])

        chart = _figure(assets, os.path.join(images_dir, f"{g}_top_centrality.png"), f"{g}: top 10 nodos por centralidad promedio")
        table = _table(headers, top10, numeric_cols=numeric)
        sections.append(f'<h2>{_e(g)}</h2><div class="chart-grid"><div>{chart}</div><div>{table}</div></div>')

    answer_bits = []
    if top_overall:
        g, row = top_overall
        answer_bits.append(
            f"En <strong>{_e(g)}</strong>, el subreddit con mayor centralidad promedio es "
            f"<strong>{_e(row['node'])}</strong> ({_fmt(row.get('average'))})."
        )
    answer_bits.append("Cada grafo usa un conjunto distinto de medidas de centralidad (ver tabla), por lo que el ranking no es directamente comparable entre grafos.")
    answer = " ".join(answer_bits) if sections else "No hay datos de centralidad en OUTPUT/raw todavía — ejecuta la etapa de centralidad primero."

    return answer, "".join(sections) if sections else "<p class=\"lede\">Sin datos.</p>"


def build_histogram_page(raw_dir, assets):
    histogram_dir = os.path.join(raw_dir, "histograms")
    fits = _read_csv(os.path.join(histogram_dir, "powerlaw_fit_summary.csv"))

    sections = []
    if os.path.isdir(histogram_dir):
        for graph in sorted(d for d in os.listdir(histogram_dir) if os.path.isdir(os.path.join(histogram_dir, d))):
            gdir = os.path.join(histogram_dir, graph)
            figs = []
            for fn in sorted(os.listdir(gdir)):
                if fn.lower().endswith(".png"):
                    metric = fn[len(graph) + 1:].rsplit(".", 1)[0]
                    figs.append(_figure(assets, os.path.join(gdir, fn), f"{graph} · {metric}"))
            if figs:
                sections.append(f'<h2>{_e(graph)}</h2><div class="chart-grid">{"".join(figs)}</div>')

    fit_table = _table(["graph", "gamma", "xmin"], fits, numeric_cols=("gamma", "xmin"))

    if fits:
        heaviest = max(fits, key=lambda r: float(r["gamma"]) if r["gamma"] not in (None, "") else -1)
        answer = (
            "El ajuste de ley de potencia sobre la distribución de grado da un exponente "
            + ", ".join(f"<strong>γ≈{_fmt(r['gamma'], 2)}</strong> en {_e(r['graph'])} (x_min={_fmt(r['xmin'], 1)})" for r in fits)
            + f". La cola más pronunciada corresponde a {_e(heaviest['graph'])}, consistente con una red libre de escala."
        )
    else:
        answer = "No hay ajustes de ley de potencia en OUTPUT/raw todavía — ejecuta la etapa de histogramas primero."

    body = f"<h2>Ajuste de ley de potencia (grado)</h2>{fit_table}" + "".join(sections)
    return answer, body


def build_small_world_page(raw_dir, assets):
    graphics_dir = os.path.join(raw_dir, "graphics")
    rows = _read_csv(os.path.join(graphics_dir, "small_world.csv"))
    chart = _figure(assets, os.path.join(graphics_dir, "small_world.png"), "Largo característico y clustering vs. referencia Erdős–Rényi")
    table = _table(["name", "k", "k_avg", "L", "L_ER", "C", "C_ER"], rows, numeric_cols=("k", "k_avg", "L", "L_ER", "C", "C_ER"))

    if rows:
        bits = []
        for r in rows:
            L, L_ER = float(r["L"]), float(r["L_ER"])
            C, C_ER = float(r["C"]), float(r["C_ER"])
            small_world = C > C_ER and L <= L_ER * 1.5
            bits.append(f"{_e(r['name'])}: {'sí' if small_world else 'no concluyente'} (C={_fmt(C)} vs C_ER={_fmt(C_ER)}, L={_fmt(L)} vs L_ER={_fmt(L_ER)})")
        answer = "¿Mundo pequeño? " + "; ".join(bits) + ". Un clustering muy superior al de un grafo aleatorio equivalente, con un largo característico comparable, es la firma de una red de mundo pequeño."
    else:
        answer = "No hay datos de mundo pequeño en OUTPUT/raw todavía — ejecuta la etapa de análisis primero."

    body = chart + table
    return answer, body


def build_assortativity_page(raw_dir, assets):
    graphics_dir = os.path.join(raw_dir, "graphics")
    rows = _read_csv(os.path.join(graphics_dir, "assortativity.csv"))
    chart = _figure(assets, os.path.join(graphics_dir, "assortativity.png"), "Coeficiente de asortatividad por grado, por grafo")
    table = _table(["graph", "assortativity"], rows, numeric_cols=("assortativity",))

    if rows:
        bits = [f"{_e(r['graph'])}: {_fmt(r['assortativity'])} ({'asortativa' if float(r['assortativity']) >= 0 else 'disortativa'})" for r in rows]
        answer = "; ".join(bits) + ". Un coeficiente positivo indica que nodos de grado similar tienden a conectarse entre sí; uno negativo, que nodos de alto grado tienden a conectarse con nodos de bajo grado."
    else:
        answer = "No hay datos de asortatividad en OUTPUT/raw todavía — ejecuta la etapa de análisis primero."

    body = chart + table
    return answer, body


def build_bowtie_page(raw_dir, assets):
    images_dir = os.path.join(raw_dir, "images")
    rows = _read_csv(os.path.join(images_dir, "bowtie_summary.csv"))
    chart = _figure(assets, os.path.join(images_dir, "bowtie_reddit.png"), "Descomposición bow-tie de AGG_REDDIT")
    table = _table(["component", "count"], rows, numeric_cols=("count",))

    counts = {r["component"]: int(float(r["count"])) for r in rows} if rows else {}
    if counts:
        total = counts.get("total", sum(v for k, v in counts.items() if k != "total")) or 1
        scc_pct = 100 * counts.get("scc", 0) / total
        answer = (
            f"El núcleo fuertemente conexo (SCC) reúne el <strong>{scc_pct:.1f}%</strong> de los "
            f"{counts.get('total', 0)} subreddits ({counts.get('scc', 0)} nodos); "
            f"IN aporta {counts.get('in_component', 0)}, OUT {counts.get('out_component', 0)} y los tendrils {counts.get('tendrils', 0)}."
        )
    else:
        answer = "No hay datos de bow-tie en OUTPUT/raw todavía — ejecuta la etapa de análisis primero."

    body = chart + table
    return answer, body


def build_models_page(raw_dir, assets):
    graphics_dir = os.path.join(raw_dir, "graphics")
    sections = []
    answers = []
    numeric = ("N", "E", "k", "L", "C", "assortativity")

    for label, stem in (("AGG_REDDIT", "models_comparison_agg"), ("CONX_REDDIT", "models_comparison_conx")):
        rows = _read_csv(os.path.join(graphics_dir, f"{stem}.csv"))
        if not rows:
            continue
        chart = _figure(assets, os.path.join(graphics_dir, f"{stem}.png"), f"Modelos sintéticos vs. {label}")
        table = _table(["name", "N", "E", "k", "L", "C", "connected", "assortativity"], rows, numeric_cols=numeric)
        sections.append(f"<h2>Comparación usando {_e(label)}</h2>" + chart + table)

        real = next((r for r in rows if r["model"] == "AGG"), None)
        closest = None
        if real:
            candidates = [r for r in rows if r["model"] != "AGG"]
            closest = min(candidates, key=lambda r: abs(float(r["C"]) - float(real["C"])), default=None)
        if real and closest:
            answers.append(
                f"En {_e(label)}, el modelo con clustering más parecido a la red real (C={_fmt(real['C'])}) "
                f"es <strong>{_e(closest['name'])}</strong> (C={_fmt(closest['C'])})."
            )

    answer = " ".join(answers) if answers else "No hay comparación de modelos en OUTPUT/raw todavía — ejecuta la etapa de modelos primero."
    return answer, "".join(sections) if sections else "<p class=\"lede\">Sin datos.</p>"


def build_main_page(raw_dir, assets, page_snippets):
    centrality_dir = os.path.join(raw_dir, "centralities", "summary")
    graphs = _find_graphs(centrality_dir)

    n_nodes = n_edges = None
    agg_rows = _read_csv(os.path.join(centrality_dir, "reddit_AGG_REDDIT_centrality_full_centrality.csv"))
    fits = _read_csv(os.path.join(raw_dir, "histograms", "powerlaw_fit_summary.csv"))
    bowtie_rows = _read_csv(os.path.join(raw_dir, "images", "bowtie_summary.csv"))
    bowtie_counts = {r["component"]: r["count"] for r in bowtie_rows}

    tiles = []
    if bowtie_counts.get("total"):
        tiles.append(("Subreddits (AGG_REDDIT)", bowtie_counts["total"]))
    if bowtie_counts.get("scc"):
        tiles.append(("Nodos en el SCC", bowtie_counts["scc"]))
    if agg_rows:
        tiles.append(("Top subreddit (AGG_REDDIT)", agg_rows[0]["node"]))
    agg_gamma = next((r for r in fits if r["graph"] == "AGG_REDDIT"), None)
    if agg_gamma:
        tiles.append(("γ ley de potencia (grado)", _fmt(agg_gamma["gamma"], 2)))
    tiles.append(("Grafos analizados", len(graphs) if graphs else "—"))

    questions = [
        ("centrality", "¿Qué subreddits son más centrales?", "centrality.html"),
        ("degree_distribution", "¿La distribución de grado sigue una ley de potencia?", "degree_distribution.html"),
        ("small_world", "¿La red exhibe propiedades de mundo pequeño?", "small_world.html"),
        ("assortativity", "¿La red es asortativa o disortativa?", "assortativity.html"),
        ("bowtie", "¿Cuál es la macroestructura (bow-tie) de la red?", "bowtie.html"),
        ("models", "¿Cómo se compara la red real con modelos sintéticos?", "models.html"),
    ]
    cards = "".join(
        f'<a class="card" href="{href}"><div class="q">{_e(q)}</div>'
        f'<div class="a">{_e(page_snippets.get(key, "Ver detalle →"))}</div></a>'
        for key, q, href in questions
    )

    answer = (
        "Este informe resume el análisis de la red de hipervínculos entre subreddits "
        "(SNAP Reddit Hyperlinks): centralidad, distribución de grado, propiedades de mundo pequeño, "
        "asortatividad, macroestructura bow-tie y comparación contra modelos sintéticos."
    )
    body = _tiles(tiles) + f'<h2>Preguntas</h2><div class="cards">{cards}</div>'
    return answer, body


def _short(text, n=110):
    text = text.replace("<strong>", "").replace("</strong>", "")
    return text if len(text) <= n else text[: n - 1] + "…"


def run(config):
    """Entry point called by scr/main.py. Reads config["paths"]["output_raw"]
    from disk and writes the finished, self-contained report to
    config["paths"]["output_pages"] (default OUTPUT/pages/final/)."""
    paths = config["paths"]
    raw_dir = paths["output_raw"]
    pages_dir = paths["output_pages"]
    img_dir = os.path.join(pages_dir, "img")
    os.makedirs(pages_dir, exist_ok=True)
    assets = AssetCopier(img_dir)

    builders = {
        "centrality": lambda: build_centrality_page(raw_dir, assets),
        "degree_distribution": lambda: build_histogram_page(raw_dir, assets),
        "small_world": lambda: build_small_world_page(raw_dir, assets),
        "assortativity": lambda: build_assortativity_page(raw_dir, assets),
        "bowtie": lambda: build_bowtie_page(raw_dir, assets),
        "models": lambda: build_models_page(raw_dir, assets),
    }
    titles = {
        "centrality": "¿Qué subreddits son más centrales?",
        "degree_distribution": "¿La distribución de grado sigue una ley de potencia?",
        "small_world": "¿La red exhibe propiedades de mundo pequeño?",
        "assortativity": "¿La red es asortativa o disortativa?",
        "bowtie": "¿Cuál es la macroestructura (bow-tie) de la red?",
        "models": "¿Cómo se compara la red real con modelos sintéticos?",
    }

    written = {}
    snippets = {}
    for key, build in builders.items():
        answer, body = build()
        snippets[key] = _short(answer)
        html_out = _page(key, f"{titles[key]} · CC5118 Redes Complejas", titles[key], answer, body)
        out_path = os.path.join(pages_dir, f"{key}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_out)
        written[key] = out_path

    main_answer, main_body = build_main_page(raw_dir, assets, snippets)
    main_html = _page("main", "Resumen · CC5118 Redes Complejas", "Análisis de la red de hipervínculos de Reddit", main_answer, main_body)
    main_path = os.path.join(pages_dir, "main.html")
    with open(main_path, "w", encoding="utf-8") as f:
        f.write(main_html)
    written["main"] = main_path

    print(f"Report written to: {pages_dir}")
    for key, path in written.items():
        print(f"\t{key}: {path}")

    return written


def publish(config):
    """Stage `publish`: copy the finished report from output_pages (ignored
    by git) to results_html (Results/html/, tracked) so it can be browsed
    from the GitHub repository. The target is replaced wholesale so images
    from older runs don't linger; an index.html redirect to main.html is
    added so a static host (e.g. GitHub Pages) serves the summary at the
    folder root."""
    paths = config["paths"]
    src = paths["output_pages"]
    dst = paths["results_html"]
    if not os.path.isfile(os.path.join(src, "main.html")):
        raise FileNotFoundError(f"No report found at {src} - run the `report` stage first.")

    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    with open(os.path.join(dst, "index.html"), "w", encoding="utf-8") as f:
        f.write('<!doctype html>\n<meta charset="utf-8">\n'
                '<meta http-equiv="refresh" content="0; url=main.html">\n'
                '<a href="main.html">Ir al reporte</a>\n')

    print(f"Report published to: {dst}")
    return dst
