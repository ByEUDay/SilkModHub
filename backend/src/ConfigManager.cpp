#include "ConfigManager.h"
#include <nlohmann/json.hpp>
#include <fstream>
#include <filesystem>

namespace fs = std::filesystem;
using json = nlohmann::json;

namespace silk {

ConfigManager::ConfigManager(std::string configPath) : configPath_(std::move(configPath)) {}

AppConfig ConfigManager::load() {
    AppConfig cfg;
    if (!fs::exists(configPath_)) {
        return cfg;
    }
    try {
        std::ifstream f(configPath_);
        json j;
        f >> j;
        cfg.gamePath = j.value("gamePath", cfg.gamePath);
        cfg.theme = j.value("theme", cfg.theme);
        cfg.community = j.value("community", cfg.community);
        cfg.checkUpdatesOnStart = j.value("checkUpdatesOnStart", cfg.checkUpdatesOnStart);
        cfg.language = j.value("language", cfg.language);
    } catch (...) {

    }
    return cfg;
}

bool ConfigManager::save(const AppConfig& config) {
    try {
        json j;
        j["gamePath"] = config.gamePath;
        j["theme"] = config.theme;
        j["community"] = config.community;
        j["checkUpdatesOnStart"] = config.checkUpdatesOnStart;
        j["language"] = config.language;

        fs::path p(configPath_);
        if (p.has_parent_path() && !fs::exists(p.parent_path())) {
            fs::create_directories(p.parent_path());
        }
        std::ofstream f(configPath_);
        f << j.dump(4);
        return true;
    } catch (...) {
        return false;
    }
}

}
