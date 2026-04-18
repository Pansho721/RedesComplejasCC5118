#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <set>
#include <map>
#include <utility>
#include <cstdint>

int threshold = 100;
typedef std::string VertexId;

struct Partition {
    int PtId; // Partition ID
    std::set<VertexId> setVertex; 
    std::set<std::pair<VertexId, VertexId>> setEdge;
    std::map<VertexId, std::set<VertexId>> degree;

    Partition(int id,
              const std::set<VertexId>& vertices,
              const std::set<std::pair<VertexId, VertexId>>& edgesSet,
              const std::map<VertexId, std::set<VertexId>>& mapDegree)
        : PtId(id),
          setVertex(vertices),
          setEdge(edgesSet),
          degree(mapDegree) {}
};

/*      HASH FUNCTION USED ON SMALL GRAPH 5
int hashInt(int x) {
    return x-1;
}*/

int hashInt(int x) {
    uint32_t v = static_cast<uint32_t>(x);

    v = (v ^ 61) ^ (v >> 16);
    v = v + (v << 3);
    v = v ^ (v >> 4);
    v = v * 0x27d4eb2d;
    v = v ^ (v >> 15);

    return static_cast<int>(v);
}

int master(std::string x, int p) {
    return (unsigned) hashInt(std::hash<std::string>{}(x)) % p;
}

void printPartition(Partition p){
    std::cout << "Partition: " << p.PtId << '\n';
    std::cout << "Number of vertices: " << p.setVertex.size() << '\n';
    std::cout << "Number of edges: " << p.setEdge.size() << '\n';
    return;
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: [executable] [input_tsv] [num_partitions]\n");
        exit(-1);
    }

    int p = atoi(argv[2]);
    std::vector<Partition> Pts;
    for (int i = 0; i < p; i++) {
        std::set<VertexId> setVertex;
        std::set<std::pair<VertexId, VertexId>> setEdge;
        std::map<VertexId, std::set<VertexId>> degree;

        Pts.emplace_back(i, setVertex, setEdge, degree);
    }
    std::ifstream fin(argv[1]);
    if (!fin) {
        std::cerr << "Error: cannot open input file.\n";
        return -1;
    }

    int e = 0;
    std::string line;
    while (std::getline(fin, line)) {
        if (line.empty()) {
            continue;
        }

        std::size_t tabPos = line.find('\t');
        if (tabPos == std::string::npos) {
            continue;
        }

        VertexId src = line.substr(0, tabPos);
        VertexId dst = line.substr(tabPos + 1);
        if (src.empty() || dst.empty()) {
            continue;
        }

        auto edge = std::make_pair(src,dst);
        int pt = master(dst,p);
        if((Pts[pt].degree[dst].size() + 1) <= threshold){
            Pts[pt].degree[dst].insert(src);
            Pts[pt].setEdge.insert(edge);
            Pts[pt].setVertex.insert(src);
            Pts[pt].setVertex.insert(dst);
        } else {
            pt = master(src,p);
            Pts[pt].setEdge.insert(edge);
            Pts[pt].setVertex.insert(src);
            Pts[pt].setVertex.insert(dst);
        }
        e++;
    }
    fin.close();

    for (int i=0; i<p; i++){
        printPartition(Pts[i]);
    }

    for (int i = 0; i < p; i++) {
        std::string fileName = "partition" + std::to_string(i) + ".graph";
        std::ofstream fout(fileName);
        if (!fout) {
            std::cerr << "Error: cannot open output file: " << fileName << "\n";
            return -1;
        }

        for (const auto &e : Pts[i].setEdge){
            fout << e.first << '\t' << e.second << '\n';
        }

        fout.close();
    }
    
    return 0;
}
