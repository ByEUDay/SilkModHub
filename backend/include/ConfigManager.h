#pragma once
#include <string>

namespace silk {


struct AppConfig {
    std::string gamePath;
    std::string theme = "silk";
    std::string community = "silksong";
    bool checkUpdatesOnStart = true;
    std::string language = "zh_CN";
};

class ConfigManager {
public:
    explicit ConfigManager(std::string configPath);

    AppConfig load();
    bool save(const AppConfig& config);

    const std::string& path() const { return configPath_; }

private:
    std::string configPath_;
};

}
