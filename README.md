# Descripcion de Balanced_p-way_Vertex-cut.cpp

Este es un script que transforma un grafo de texto plano en una particion del grafo usando el algoritmo de vertex cut, es decir, selecciona una conjunto de vertices de forma equitativa y los define como parte de una de las particiones, a estos nodos se le llama masters, luego inserta todos los arcos que contengan a este nodo, los nodos que no pertenecian a los masters de la particiones se le conocen como mirrors.

# Descripcion de funciones principales en read.py

- *CreateGraph_from_file(path, sep='\t', head=10, cols=None, count=False):*
    - lee un archivo tabular, selecciona columnas y construye un grafo dirigido usando pares origen-destino.
- *create_reddit_edgelist_from_file(input_path, output_path='graph.edgelist', sep='\t'):*
    - usa CreateGraph_from_file para extraer SOURCE_SUBREDDIT y TARGET_SUBREDDIT y guarda el resultado como edgelist.
- *load_graph_from_edgelist(path, sep='\t'):*
    - carga un archivo de aristas en texto plano y lo convierte en un grafo dirigido.
- *load_node_set(path):*
    - lee un archivo con un nodo por linea y devuelve un conjunto de nodos.
- *write_partition_graphs(num_partitions=8, file_prefix='partition/'):*
    - carga los grafos de cada particion y adjunta sus nodos master y mirror desde carpetas separadas.
- *draw_and_save_graph(G, out_path, title, node_size=8, fig_size=(20, 20), dpi=50):*
    - dibuja el grafo, colorea nodos por tipo (master/mirror) y guarda la imagen.
- *plot_partitions():*
    - recorre las particiones, genera una imagen para cada una y la guarda como graph_i.png.
- *plot_graph():*
    - carga el grafo completo desde graph.edgelist y guarda su visualizacion general.
- *plot_all():*
    - ejecuta ambos procesos, visualizacion global y visualizaciones por particion.

