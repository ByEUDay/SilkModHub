#include "GameDetector.h"
#include <filesystem>
#include <fstream>
#include <sstream>
#include <cstdlib>
#include <algorithm>

namespace fs = std::filesystem;

namespace silk {

GameDetector::GameDetector() = default;

bool GameDetector::looksLikeSilksongDir(const std::string& path) {
    if (!fs::exists(path) || !fs::is_directory(path)) return false;
#if defined(_WIN32)
    return fs::exists(fs::path(path) / kExeNameWin);
#elif defined(__APPLE__)
    return fs::exists(fs::path(path) / kExeNameMac);
#else
    return fs::exists(fs::path(path) / kExeNameLinux);
#endif
}

std::vector<std::string> GameDetector::steamLibraryFolders() {
    std::vector<std::string> libs;

    std::vector<std::string> candidates;
#if defined(_WIN32)
    const char* programFilesX86 = std::getenv("ProgramFiles(x86)");
    const char* programFiles = std::getenv("ProgramFiles");
    if (programFilesX86) candidates.push_back(std::string(programFilesX86) + "\\Steam");
    if (programFiles) candidates.push_back(std::string(programFiles) + "\\Steam");
#elif defined(__APPLE__)
    const char* home = std::getenv("HOME");
    if (home) candidates.push_back(std::string(home) + "/Library/Application Support/Steam");
#else
    const char* home = std::getenv("HOME");
    if (home) {
        candidates.push_back(std::string(home) + "/.steam/steam");
        candidates.push_back(std::string(home) + "/.local/share/Steam");
        candidates.push_back(std::string(home) + "/.var/app/com.valvesoftware.Steam/data/Steam");
    }
#endif

    for (auto& base : candidates) {
        if (!fs::exists(base)) continue;
        libs.push_back((fs::path(base) / "steamapps" / "common").string());


        fs::path vdf = fs::path(base) / "steamapps" / "libraryfolders.vdf";
        if (fs::exists(vdf)) {
            std::ifstream f(vdf);
            std::string line;
            while (std::getline(f, line)) {
                auto pos = line.find("\"path\"");
                if (pos == std::string::npos) continue;
                auto first = line.find('"', pos + 6);
                auto second = line.find('"', first + 1);
                if (first == std::string::npos || second == std::string::npos) continue;
                std::string libPath = line.substr(first + 1, second - first - 1);

                std::string cleaned;
                for (size_t i = 0; i < libPath.size(); ++i) {
                    if (libPath[i] == '\\' && i + 1 < libPath.size() && libPath[i+1] == '\\') {
                        cleaned += '\\';
                        ++i;
                    } else {
                        cleaned += libPath[i];
                    }
                }
                libs.push_back((fs::path(cleaned) / "steamapps" / "common").string());
            }
        }
    }
    return libs;
}

std::optional<GameInstall> GameDetector::scanSteamLibrary(const std::string& libraryPath) {
    if (!fs::exists(libraryPath)) return std::nullopt;
    for (auto& entry : fs::directory_iterator(libraryPath)) {
        if (!entry.is_directory()) continue;
        auto name = entry.path().filename().string();
        std::string lower = name;
        std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
        if (lower.find("silksong") != std::string::npos ||
            lower.find("hollow knight silksong") != std::string::npos) {
            if (looksLikeSilksongDir(entry.path().string())) {
                GameInstall gi;
                gi.path = entry.path().string();
                gi.source = "steam";
                gi.valid = true;
#if defined(_WIN32)
                gi.executable = (entry.path() / kExeNameWin).string();
#elif defined(__APPLE__)
                gi.executable = (entry.path() / kExeNameMac).string();
#else
                gi.executable = (entry.path() / kExeNameLinux).string();
#endif
                return gi;
            }
        }
    }
    return std::nullopt;
}

std::optional<GameInstall> GameDetector::detect() {
    for (auto& lib : steamLibraryFolders()) {
        auto found = scanSteamLibrary(lib);
        if (found) return found;
    }


#if defined(_WIN32)
    std::vector<std::string> gogCandidates = {
        "C:\\GOG Games\\Hollow Knight Silksong",
        "C:\\Program Files (x86)\\GOG Galaxy\\Games\\Hollow Knight Silksong"
    };
    for (auto& c : gogCandidates) {
        if (looksLikeSilksongDir(c)) {
            GameInstall gi;
            gi.path = c;
            gi.source = "gog";
            gi.valid = true;
            gi.executable = (fs::path(c) / kExeNameWin).string();
            return gi;
        }
    }
#endif

    return std::nullopt;
}

GameInstall GameDetector::validateManualPath(const std::string& path) {
    GameInstall gi;
    gi.path = path;
    gi.source = "manual";
    gi.valid = looksLikeSilksongDir(path);
    if (gi.valid) {
#if defined(_WIN32)
        gi.executable = (fs::path(path) / kExeNameWin).string();
#elif defined(__APPLE__)
        gi.executable = (fs::path(path) / kExeNameMac).string();
#else
        gi.executable = (fs::path(path) / kExeNameLinux).string();
#endif
    }
    return gi;
}

std::string GameDetector::getModsDirectory(const GameInstall& install) {


    fs::path modsDir = fs::path(install.path) / "BepInEx" / "plugins";
    if (!fs::exists(modsDir)) {
        fs::create_directories(modsDir);
    }
    return modsDir.string();
}

std::string GameDetector::getLoaderDirectory(const GameInstall& install) {

    fs::path loaderDir = fs::path(install.path) / "BepInEx";
    if (!fs::exists(loaderDir)) {
        fs::create_directories(loaderDir);
    }
    return loaderDir.string();
}

}
