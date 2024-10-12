#ifndef CONFIG_UTILS_HH
#define CONFIG_UTILS_HH

#include <unordered_map>
#include <vector>
#include <nlohmann/json.hpp>
#include <fstream> 
#include <optional>

using json = nlohmann::json;
using namespace std;

void writeJSONToFile(const nlohmann::json &j, const string &filename);
#endif 