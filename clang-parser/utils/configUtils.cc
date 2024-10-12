#include "configUtils.hh"
using json = nlohmann::json;
using namespace std;


void writeJSONToFile(const json &j, const string &filename) {
    ofstream file(filename);
    file << j.dump(4);  // 4 spaces for indentation
}


