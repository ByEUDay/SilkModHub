#pragma once
#include <string>
#include <vector>
#include <map>
#include <functional>

namespace silk {


struct InstalledMod {
    std::string uuid;
    std::string name;
    std::string author;
    std::string version;
    std::string description;
    std::string installPath;
    bool enabled = true;
    bool isDependencyOnly = false;
};


using ProgressCallback = std::function<void(long current, long total, const std::string& stage)>;


class ModManager {
public:
    explicit ModManager(std::string gameModsDir, std::string dataDir);


    void loadLocalManifest();

    void saveLocalManifest();

    const std::vector<InstalledMod>& installedMods() const { return mods_; }


    bool installFromZip(const std::string& zipPath,
                         const std::string& uuid,
                         const std::string& name,
                         const std::string& author,
                         const std::string& version,
                         const std::string& description,
                         ProgressCallback onProgress = nullptr);

    bool uninstall(const std::string& uuid);
    bool setEnabled(const std::string& uuid, bool enabled);
    bool isInstalled(const std::string& uuid) const;
    std::string installedVersion(const std::string& uuid) const;

private:
    std::string gameModsDir_;
    std::string dataDir_;
    std::vector<InstalledMod> mods_;

    std::string manifestPath() const;
    bool extractZip(const std::string& zipPath, const std::string& destDir);

    std::string disabledMarkerPath(const InstalledMod& mod) const;
};

}
