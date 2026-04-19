#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <set>
#include <utility>
#include <cstdint>
#include <sys/stat.h>


typedef std::string VertexId;

struct Partition {
    int PtId; // Partition ID
    std::set<VertexId> setVertex; // Set of vertices
    std::set<VertexId> setMaster; // Set of masters
    std::set<std::pair<VertexId, VertexId>> setEdge; // Set of edges represented as pairs of vertices

    Partition(int id,
              const std::set<VertexId>& vertices,
              const std::set<VertexId>& master,
              const std::set<std::pair<VertexId, VertexId>>& edgesSet)
        : PtId(id),
          setVertex(vertices), setMaster(master), setEdge(edgesSet) {}
};

/*      HASH FUNCTION TO SMALL GRAPH 5
int hashInt(int x) {
    return x -1;
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
    std::cout << "Partition " << p.PtId << '\n';
    std::cout << "Number of master vertices: " << p.setMaster.size() << '\n';
    std::cout << "Number of total vertices: " << p.setVertex.size()+p.setMaster.size() << '\n';
    std::cout << "Number of edges in this partition: " << p.setEdge.size() << '\n';
    return;
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: [executable] [input]\n");
        exit(-1);
    }

    int p = atoi(argv[2]);
    std::vector<Partition> Pts;
    for (int i=0; i<p ; i++){
        std::set<VertexId> setVertex;
        std::set<VertexId> setMaster;
        std::set<std::pair<VertexId, VertexId>> setEdge;
        Pts.emplace_back(i, setVertex, setMaster, setEdge);
    }


    std::ifstream fin(argv[1]);
    if (!fin) {
        std::cerr << "Error: cannot open input file.\n";
        return -1;
    }
    int e = 1;
    VertexId src, dst;
    while (fin >> src >> dst) {
        auto edge = std::make_pair(src,dst);
        int whichP = master(std::to_string(e),p);
        int msrc = master(src,p);
        int mdst = master(dst,p);
        std::cout << whichP << ' ' << src << ' ' << dst << '\n';

        Pts[msrc].setMaster.insert(src);
        Pts[mdst].setMaster.insert(dst);
        Pts[whichP].setEdge.insert(edge);
        if (msrc != whichP){
            Pts[whichP].setVertex.insert(src);
        }
        if (mdst != whichP){
            Pts[whichP].setVertex.insert(dst);
        }
        e++;
    }

    for (int i=0; i<p; i++){
        printPartition(Pts[i]);
    }


    
    mkdir("partition", 0755);
    mkdir("partitionMaster", 0755);
    mkdir("partitionMirror", 0755);

    for (int i = 0; i < p; i++) {
        std::string partitionFileName = "partition/" + std::to_string(i) + ".graph";
        std::string masterFileName = "partitionMaster/" + std::to_string(i) + "_master.graph";
        std::string mirrorFileName = "partitionMirror/" + std::to_string(i) + "_mirror.graph";
        std::ofstream pout(partitionFileName);
        std::ofstream maout(masterFileName);
        std::ofstream miout(mirrorFileName);

        if (!pout || !maout || !miout) {
            std::cerr << "Error: cannot open output file.\n";
            return -1;
        }

        for (const auto &v : Pts[i].setMaster) {
            maout << v  << "\n";
        }
        for (const auto &v : Pts[i].setVertex) {
            miout << v  << "\n";
        }
        for (const auto &e : Pts[i].setEdge) {
            pout << e.first << '\t' << e.second << "\n";
        }
    }

    return 0;
}
