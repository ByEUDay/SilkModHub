#pragma once
#include <string>
#include <vector>
#include <optional>

namespace silk {


struct GameInstall {
    std::string path;
    std::string executable;
    std::string source;
    bool valid = false;
};


class GameDetector {
public:
    GameDetector();


    std::optional<GameInstall> detect();


    GameInstall validateManualPath(const std::string& path);


    std::string getModsDirectory(const GameInstall& install);


    std::string getLoaderDirectory(const GameInstall& install);

private:
    std::vector<std::string> steamLibraryFolders();
    std::optional<GameInstall> scanSteamLibrary(const std::string& libraryPath);
    bool looksLikeSilksongDir(const std::string& path);

    static constexpr const char* kSteamAppId = "1030300";
    static constexpr const char* kExeNameWin = "Hollow Knight Silksong.exe";
    static constexpr const char* kExeNameLinux = "Hollow Knight Silksong.x86_64";
    static constexpr const char* kExeNameMac = "Hollow Knight Silksong.app";
};

}
