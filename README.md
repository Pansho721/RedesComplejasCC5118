# Descripcion general de Funcionamiento

## Inicio

Para comenzar hay que configurar un ambiente virtual para poder usar las librerias necesarias.

para ello usamos el siguiente comando:

> $python3 -m venv venv

Esto crea un ambiente virtual llamado venv, en linux, una vez creado lo podemos asignar a la terminal con:

> $source ./venv/bin/activate

Esto es para poder instalar las librerias a usar, las cuales son:

+ networkx
+ matplotlib
+ joblib
+ pandas
+ scipy

Una vez inicializada el ambiente virtual instalamos las librerias desde el archivo "requirements.txt".

> $pip install -r requirements.txt

## Aplicaciones

Este proyecto abarca cuatro objetivos principales:
- Generar archivos que representan grafos facil de usar desde el dataset soc-redditHyperlinks-body.tsv
- Graficar los grafos.
- Calcular medidas de centralidad para cada grafo interezante de analizar.
- Realizar análisis de redes adicionales como small-world, assortativity y bow-tie.


### Preproceso

El preproceso genera distintos listados en texto plano que representan grafos, para ello se lee el archivo tsv y se genera los grafos desde esta lectura, luego se usan estos grafos elementales para generar grafos especificos.

| *Nombre* | *Archivo* | *Tipo* | *Descripcion* |
|:---------:|:---------|:--------:|:----------|
| _Dataset_ | soc-redditHyperlinks-body.tsv | Input, verboso | Dataset original con todas las etiquetas. | 
| _Edgelist_ | graphs/reddit.edgelist | Output, armado desde _Dataset_ | Lista simple de arcos, hay repeticiones del mismo arco, solo tiene (Source, Target) |
| _Weighted_ | graphs/reddit_weighted.edgelist | Output, armado desde _Dataset_ | Lista de arcos con peso, hay repeticiones del mismo arco, modela el sentimiento con recorrido {-1, 1} |
| _Aggregated_ | graphs/reddit_weighted_aggregated.edgelist | Output, armado desde _Weighted_ | Lista de arcos en donde se suman los arcos iguales y se definen como peso |
| _Positive_ | graphs/reddit_positive.edgelist | Output, armado desde _Weighted_ | lista de arcos, es el sub conjunto con etiquetas positiva de Aggregated |
| _Negative_ | graphs/reddit_negative.edgelist | Output, armado desde _Weighted_ | lista de arcos, es el sub conjunto con etiquetas negativa de Aggregated |
| _Summary_ | graphs/reddit_summary.txt | Output, armado desde _Positive_ y _Negative_ | Lista de arcos con todos los datos en el siuiente orden: source, destino , negegativos, positivos, total, proporcion de negativos, proporcion de positivos. |

### Graficar

Para graficar hay dos scripts, uno en C++ y otro en python.

#### Balanced_p-way_Vertex-cut.cpp

Este es un script que transforma un grafo de texto plano en una particion del grafo usando el algoritmo de vertex cut, es decir, selecciona una conjunto de vertices de forma equitativa y los define como parte de una de las particiones, a estos nodos se le llama masters, luego inserta todos los arcos que contengan a este nodo, los nodos que no pertenecian a los masters de la particiones se le conocen como mirrors.

    - Dada una lista de arcos simple devuelve una particion del grafo.

En linux usando g++, el uso es el siguiente:

> $g++ Balanced_p-way_Vertex-cut.cpp

> $./a.out *edgelist* *N*

Donde _edgelist_ corresponde a la direccion donde esta la lista de arcos y _N_ el numero de particiones.
Esto crea los directorios partition, partition Master y partition Mirror, los cuales respectivamente son: Para la lista de arcos, nodos asignados a la particion y nodos duplicados.

#### plot.py

- *load_graph_from_edgelist(path, kind='DiGraph', sep='\t'):*
    - carga un archivo de aristas en texto plano y lo convierte en un grafo del tipo indicado (DiGraph, Graph, MultiDiGraph, MultiGraph). Soporta arcos con 2, 3 o 4 columnas asignando pesos segun corresponda.
- *load_node_set(path):*
    - lee un archivo con un nodo por linea y devuelve un conjunto de nodos.
- *write_partition_graphs(num_partitions=8, file_prefix='partition/'):*
    - carga los grafos de cada particion y adjunta sus nodos master y mirror desde carpetas separadas.
- *draw_and_save_graph(G, out_path, title, node_size=8, fig_size=(20, 20), dpi=50):*
    - dibuja el grafo, colorea nodos por tipo (master/mirror) y guarda la imagen.
- *plot_partitions():*
    - recorre las particiones, genera una imagen para cada una y la guarda como graph_i.png.
- *plot_graph(path='graphs/reddit.edgelist', title='Full graph', size=(80, 80), dpi=30, sep='\t'):*
    - carga el grafo desde el archivo indicado y guarda su visualizacion general en img/graph.png.

### Centralidad

Para esta seccion el proyecto cuenta con un script que calcula la centralidad de distintos grafos

#### centrality.py

- *compute_centrality(graph, kind='degree'):*
    - calcula la medida de centralidad indicada para el grafo dado. Soporta los tipos: degree, in-degree, out-degree, betweenness, closeness, alpha-centrality y pagerank.
- *get_some_centrality(graph, kinds=['degree', 'betweenness', 'alpha-centrality']):*
    - calcula todas las medidas de centralidad indicadas y retorna un diccionario con los resultados.
- *save_centrality(dict, output_name):*
    - guarda cada medida de centralidad en un archivo CSV separado con el formato {output_name}_{kind}.csv, ordenado de mayor a menor.
- *join(output, prefix, sufix, kinds):*
    - une los archivos CSV de cada medida de centralidad en un solo archivo, agregando una columna de promedio entre todas las medidas.
- *print_typst_table(path, kinds):*
    - lee el archivo CSV de centralidad completo e imprime los 10 nodos con mayor promedio en formato de tabla typst.
- *stats(input, graph, kinds):*
    - imprime estadísticas básicas (máximo, mínimo y promedio) para cada medida de centralidad en un archivo centralizado.

Ademas en esta seccion hay un segmento de codigo para calcular la medidad de centralidad betweenness en paralelo, esta fue sacada de la documentacion oficial de NetworkX.

### Analysis

Se agregó un nuevo script de análisis de redes.

#### analysis.py

- Realiza small-world analysis comparando la longitud caracteristica y el coeficiente de clustering con un grafo de Erdős–Rényi.
- Calcula assortativity para el grafo negativo.
- Descompone el grafo agregado en Bow-tie: SCC, IN, OUT y Tendrils.
- Genera una visualización de la estructura Bow-tie en `img/bowtie_reddit.png`.
- Utiliza los grafos:
    - `graphs/reddit_weighted_aggregated.edgelist`
    - `graphs/reddit_negative.edgelist`
    - el mayor componente fuertemente conectado de `AGG_REDDIT`.
