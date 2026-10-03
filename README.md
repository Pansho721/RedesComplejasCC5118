# Descripcion general de Funcionamiento

Analisis de la red de hipervinculos entre subreddits (dataset SNAP "Reddit Hyperlinks") para el curso CC5118 (Redes Complejas): centralidad, distribucion de grado, propiedades de mundo pequeno, asortatividad, macroestructura bow-tie y comparacion contra modelos sinteticos. El resultado final es un reporte HTML donde cada pagina responde una pregunta de analisis, mas una pagina de resumen.

## Resultados

El reporte final esta versionado en [`Results/html/`](Results/html/): siete paginas HTML autocontenidas (`main.html` es el resumen y punto de entrada; `index.html` redirige a el) con todas sus imagenes en `Results/html/img/`. No dependen de recursos externos ni de los datos crudos.

Para verlo, clona el repositorio y abre `Results/html/main.html` en un navegador. GitHub muestra el codigo fuente de los `.html` en vez de renderizarlos; para verlos en linea hay que publicar la carpeta con GitHub Pages.

`Results/html/` se regenera con la etapa `publish` del pipeline (ver abajo), que reemplaza la carpeta completa con el contenido de `OUTPUT/pages/final/`. Para actualizar los resultados del repositorio hay que correr el pipeline completo (o `--only report,publish` si `OUTPUT/raw/` ya esta al dia) y commitear `Results/`.

## Estructura del proyecto

```
INPUT/raw/soc-redditHyperlinks-body.tsv   # dataset original (descargado manualmente)
INPUT/edgelist/                           # edgelists derivados del TSV (generados)

OUTPUT/raw/centralities/                  # CSV de centralidad por grafo/medida (+ summary/)
OUTPUT/raw/histograms/                    # PNG de distribucion de grado + ajuste ley de potencia
OUTPUT/raw/images/                        # figuras principales (top-centralidad, bow-tie)
OUTPUT/raw/graphics/                      # figuras de comparacion (mundo pequeno, asortatividad, modelos)
OUTPUT/pages/final/                       # reporte HTML autocontenido (main.html + img/)
Results/html/                             # copia versionada del reporte (etapa publish)

setup.sh              # valida el entorno y lanza el pipeline
scr/main.py            # orquestador: todos los parametros ajustables viven aqui
scr/preprocess.py       # TSV -> edgelists
scr/graph_io.py          # carga de edgelists compartida por el resto de etapas
scr/centrality.py         # medidas de centralidad (tabla lazy de dispatch)
scr/histogram.py           # histogramas de distribucion de grado + ajuste ley de potencia
scr/analysis.py             # mundo pequeno, asortatividad, bow-tie
scr/models.py                 # comparacion contra modelos sinteticos (tabla lazy de dispatch)
scr/report.py                  # genera el reporte HTML a partir de OUTPUT/raw
scr/palette.py                   # paleta de colores compartida por los graficos y el HTML
```

## Inicio

`setup.sh` deja el entorno listo antes de correr nada: crea/activa el `venv`, instala dependencias, hace un chequeo de compilacion de `scr/`, prueba que cada libreria (`networkx`, `matplotlib`, `pandas`, `numpy`, `scipy`, `powerlaw`) se pueda importar, y valida que `INPUT/raw/soc-redditHyperlinks-body.tsv` tenga las columnas esperadas.

```bash
./setup.sh
```

Al terminar los chequeos, `setup.sh` ejecuta el pipeline completo (`python3 scr/main.py`). Para solo validar el entorno sin correr el pipeline:

```bash
./setup.sh --check-only
```

El dataset `soc-redditHyperlinks-body.tsv` no esta incluido en el repositorio: hay que descargarlo desde https://snap.stanford.edu/data/soc-RedditHyperlinks.html y colocarlo en `INPUT/raw/`.

## Ejecutar el pipeline directamente

```bash
source venv/bin/activate
python3 scr/main.py [--verbose] [--only preprocess,centrality,histogram,analysis,models,report,publish]
```

Todos los parametros ajustables (rutas, que medidas de centralidad calcular por grafo, overrides de parametros de modelos) viven en el diccionario `CONFIG` al inicio de `scr/main.py` — no hace falta tocar los modulos de `scr/` para cambiarlos.

### Etapas

1. **Preprocess** (`scr/preprocess.py`): lee el TSV y genera los distintos edgelists en `INPUT/edgelist/`.

| *Nombre* | *Archivo* | *Descripcion* |
|:---------:|:---------|:----------|
| _Dataset_ | `INPUT/raw/soc-redditHyperlinks-body.tsv` | Dataset original con todas las etiquetas. |
| _Edgelist_ | `INPUT/edgelist/reddit.edgelist` | Lista simple de arcos, con repeticiones, solo (Source, Target). |
| _Weighted_ | `INPUT/edgelist/reddit_weighted.edgelist` | Lista de arcos con peso, con repeticiones, modela el sentimiento con recorrido {-1, 1}. |
| _Aggregated_ | `INPUT/edgelist/reddit_weighted_aggregated.edgelist` | Arcos iguales sumados y definidos como peso ("AGG_REDDIT"). |
| _Positive_ | `INPUT/edgelist/reddit_positive.edgelist` | Subconjunto con etiqueta positiva de Aggregated. |
| _Negative_ | `INPUT/edgelist/reddit_negative.edgelist` | Subconjunto con etiqueta negativa de Aggregated ("NEG_REDDIT"). |
| _Summary_ | `INPUT/edgelist/reddit_summary.txt` | source, destino, negativos, positivos, total, proporcion de negativos, proporcion de positivos. |

2. **Centralidad** (`scr/centrality.py`): calcula, para `AGG_REDDIT`, `CONX_REDDIT` (mayor componente fuertemente conexo de AGG_REDDIT) y `NEG_REDDIT`, las medidas configuradas en `CONFIG["centrality_kinds"]` (degree, in/out-degree, betweenness, closeness, alpha-centrality, pagerank). Las medidas mismas son una tabla lazy `CENTRALITY_FUNCS = [(nombre, fn), ...]`, facil de extender. Guarda un CSV por medida y uno combinado con promedio en `OUTPUT/raw/centralities/`, mas un grafico de barras del top-10 en `OUTPUT/raw/images/`.

3. **Histogramas** (`scr/histogram.py`): para cada CSV de centralidad, construye un grafico log-log de frecuencia y, para el grado, un ajuste de ley de potencia (paquete `powerlaw`). Salida en `OUTPUT/raw/histograms/`.

4. **Analysis** (`scr/analysis.py`): small-world (comparando L y C contra un grafo Erdos-Renyi equivalente), asortatividad por grado, y descomposicion bow-tie (SCC, IN, OUT, Tendrils) de AGG_REDDIT. Las tres son una lista lazy `ANALYSES = [(nombre, fn), ...]`. Salida en `OUTPUT/raw/images/` y `OUTPUT/raw/graphics/`.

5. **Models** (`scr/models.py`): compara AGG_REDDIT/CONX_REDDIT contra Erdos-Renyi, Barabasi-Albert, Dual Barabasi-Albert y Holme-Kim (parametros estimados desde los datos reales). Los modelos son una tabla lazy `MODEL_BUILDERS = [(nombre, build_fn), ...]`. Corre en paralelo con `ProcessPoolExecutor`. Salida en `OUTPUT/raw/graphics/`.

6. **Report** (`scr/report.py`): lee unicamente `OUTPUT/raw/` (CSVs + PNGs ya escritos por las etapas anteriores) y genera el reporte final en `OUTPUT/pages/final/`: una pagina HTML por pregunta (`centrality.html`, `degree_distribution.html`, `small_world.html`, `assortativity.html`, `bowtie.html`, `models.html`) mas un resumen (`main.html`). Todas las imagenes referenciadas se copian a `OUTPUT/pages/final/img/`, asi que esa carpeta se puede mover o comprimir como una unidad autocontenida.

7. **Publish** (`report.publish` en `scr/report.py`): copia `OUTPUT/pages/final/` a `Results/html/` (ruta configurable en `CONFIG["paths"]["results_html"]`), reemplazando la carpeta anterior para no dejar imagenes viejas, y agrega un `index.html` que redirige a `main.html`. `OUTPUT/` esta en `.gitignore`; `Results/html/` (incluidos sus PNG) si se versiona.

## Notas

- `CONX_REDDIT` no se guarda como archivo: se deriva en cada etapa que lo necesita a partir de `AGG_REDDIT` (`nx.strongly_connected_components`).
- Varios modulos imprimen tablas en formato [Typst](https://typst.app) (`[*node*], [valor],`) ademas de guardar los datos — es intencional, para pegar directo en el informe del curso, no un error de formato.
- Betweenness centrality y la comparacion de modelos corren en paralelo (`multiprocessing`/`ProcessPoolExecutor`) sobre `CONX_REDDIT` (~11 mil nodos): en equipos con poca RAM esto puede ser el cuello de botella del pipeline.
