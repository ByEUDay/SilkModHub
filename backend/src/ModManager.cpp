#include "ModManager.h"
#include <nlohmann/json.hpp>
#include <miniz.h>
#include <filesystem>
#include <fstream>
#include <algorithm>
#include <cctype>
#include <set>
#include <vector>

namespace fs = std::filesystem;
using json = nlohmann::json;

namespace silk {

ModManager::ModManager(std::string gameModsDir, std::string dataDir)
    : gameModsDir_(std::move(gameModsDir)), dataDir_(std::move(dataDir)) {
    if (!fs::exists(gameModsDir_)) fs::create_directories(gameModsDir_);
    if (!fs::exists(dataDir_)) fs::create_directories(dataDir_);
}

std::string ModManager::manifestPath() const {
    return (fs::path(dataDir_) / "mods.json").string();
}

void ModManager::loadLocalManifest() {
    mods_.clear();
    auto p = manifestPath();
    if (!fs::exists(p)) return;
    try {
        std::ifstream f(p);
        json j;
        f >> j;
        for (auto& item : j) {
            InstalledMod m;
            m.uuid = item.value("uuid", "");
            m.name = item.value("name", "");
            m.author = item.value("author", "");
            m.version = item.value("version", "");
            m.description = item.value("description", "");
            m.installPath = item.value("installPath", "");
            m.enabled = item.value("enabled", true);
            m.isDependencyOnly = item.value("isDependencyOnly", false);
            mods_.push_back(std::move(m));
        }
    } catch (...) {

    }
}

void ModManager::saveLocalManifest() {
    json j = json::array();
    for (auto& m : mods_) {
        json item;
        item["uuid"] = m.uuid;
        item["name"] = m.name;
        item["author"] = m.author;
        item["version"] = m.version;
        item["description"] = m.description;
        item["installPath"] = m.installPath;
        item["enabled"] = m.enabled;
        item["isDependencyOnly"] = m.isDependencyOnly;
        j.push_back(item);
    }
    std::ofstream f(manifestPath());
    f << j.dump(4);
}

namespace {


const char* kLangDirKeywords[] = {
    "lang", "language", "languages", "i18n", "locale", "locales",
    "translation", "translations"
};

std::string toLower(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                    [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return s;
}


bool shouldExtract(const std::string& memberName) {
    fs::path p(memberName);
    if (!p.has_filename()) return false;
    std::string fname = toLower(p.filename().string());
    if (fname.size() >= 4 && fname.compare(fname.size() - 4, 4, ".dll") == 0) {
        return true;
    }
    for (const auto& part : p.parent_path()) {
        std::string dirName = toLower(part.string());
        for (const char* kw : kLangDirKeywords) {
            if (dirName == kw) return true;
        }
    }
    return false;
}


fs::path destRelPath(const std::string& memberName) {
    fs::path p(memberName);
    fs::path fname = p.filename();
    std::string lowerFname = toLower(fname.string());
    if (lowerFname.size() >= 4 && lowerFname.compare(lowerFname.size() - 4, 4, ".dll") == 0) {
        return fname;
    }
    fs::path parent = p.parent_path();
    fs::path accum;
    bool matched = false;
    std::vector<fs::path> segments(parent.begin(), parent.end());
    for (size_t i = 0; i < segments.size(); ++i) {
        std::string dirName = toLower(segments[i].string());
        bool isLangDir = false;
        for (const char* kw : kLangDirKeywords) {
            if (dirName == kw) { isLangDir = true; break; }
        }
        if (isLangDir || matched) {
            matched = true;
            accum /= segments[i];
        }
    }
    if (!matched) return fname;
    return accum / fname;
}

}

bool ModManager::extractZip(const std::string& zipPath, const std::string& destDir) {
    mz_zip_archive zipArchive;
    memset(&zipArchive, 0, sizeof(zipArchive));

    if (!mz_zip_reader_init_file(&zipArchive, zipPath.c_str(), 0)) {
        return false;
    }

    bool ok = true;
    std::set<std::string> seenDllNames;
    mz_uint fileCount = mz_zip_reader_get_num_files(&zipArchive);
    for (mz_uint i = 0; i < fileCount; ++i) {
        mz_zip_archive_file_stat stat;
        if (!mz_zip_reader_file_stat(&zipArchive, i, &stat)) { ok = false; break; }

        if (mz_zip_reader_is_file_a_directory(&zipArchive, i)) {
            continue;
        }

        std::string memberName = stat.m_filename;
        if (!shouldExtract(memberName)) {
            continue;
        }

        fs::path relPath = destRelPath(memberName);
        std::string lowerName = toLower(relPath.filename().string());
        bool isDll = lowerName.size() >= 4 &&
                     lowerName.compare(lowerName.size() - 4, 4, ".dll") == 0;
        if (isDll) {


            if (seenDllNames.count(lowerName)) continue;
            seenDllNames.insert(lowerName);
        }

        fs::path outPath = fs::path(destDir) / relPath;

        if (outPath.has_parent_path() && !fs::exists(outPath.parent_path())) {
            fs::create_directories(outPath.parent_path());
        }

        if (!mz_zip_reader_extract_to_file(&zipArchive, i, outPath.string().c_str(), 0)) {
            ok = false;
            break;
        }
    }

    mz_zip_reader_end(&zipArchive);
    return ok;
}

bool ModManager::installFromZip(const std::string& zipPath,
                                 const std::string& uuid,
                                 const std::string& name,
                                 const std::string& author,
                                 const std::string& version,
                                 const std::string& description,
                                 ProgressCallback onProgress) {
    if (onProgress) onProgress(0, 100, "正在解压模组文件");

    fs::path destDir = fs::path(gameModsDir_) / uuid;
    if (fs::exists(destDir)) {
        fs::remove_all(destDir);
    }
    fs::create_directories(destDir);

    if (!extractZip(zipPath, destDir.string())) {
        if (onProgress) onProgress(0, 100, "解压失败");
        return false;
    }

    bool hasDll = false;
    for (const auto& entry : fs::recursive_directory_iterator(destDir)) {
        if (entry.is_regular_file() && toLower(entry.path().extension().string()) == ".dll") {
            hasDll = true;
            break;
        }
    }
    if (!hasDll) {


        fs::remove_all(destDir);
        if (onProgress) onProgress(0, 100, "安装失败：压缩包内未找到 .dll 文件");
        return false;
    }

    if (onProgress) onProgress(90, 100, "正在登记模组信息");


    auto it = std::find_if(mods_.begin(), mods_.end(),
                            [&](const InstalledMod& m) { return m.uuid == uuid; });
    InstalledMod mod;
    mod.uuid = uuid;
    mod.name = name;
    mod.author = author;
    mod.version = version;
    mod.description = description;
    mod.installPath = destDir.string();
    mod.enabled = true;

    if (it != mods_.end()) {
        *it = mod;
    } else {
        mods_.push_back(mod);
    }
    saveLocalManifest();

    if (onProgress) onProgress(100, 100, "安装完成");
    return true;
}

bool ModManager::uninstall(const std::string& uuid) {
    auto it = std::find_if(mods_.begin(), mods_.end(),
                            [&](const InstalledMod& m) { return m.uuid == uuid; });
    if (it == mods_.end()) return false;

    std::error_code ec;
    fs::remove_all(it->installPath, ec);
    fs::remove_all(it->installPath + ".disabled", ec);

    mods_.erase(it);
    saveLocalManifest();
    return true;
}

std::string ModManager::disabledMarkerPath(const InstalledMod& mod) const {
    return mod.installPath + ".disabled";
}

bool ModManager::setEnabled(const std::string& uuid, bool enabled) {
    auto it = std::find_if(mods_.begin(), mods_.end(),
                            [&](InstalledMod& m) { return m.uuid == uuid; });
    if (it == mods_.end()) return false;
    if (it->enabled == enabled) return true;

    std::error_code ec;
    if (enabled) {

        std::string disabledPath = it->installPath + ".disabled";
        if (fs::exists(disabledPath)) {
            fs::rename(disabledPath, it->installPath, ec);
        }
    } else {
        std::string disabledPath = it->installPath + ".disabled";
        if (fs::exists(it->installPath)) {
            fs::rename(it->installPath, disabledPath, ec);
        }
    }
    if (ec) return false;

    it->enabled = enabled;
    saveLocalManifest();
    return true;
}

bool ModManager::isInstalled(const std::string& uuid) const {
    return std::any_of(mods_.begin(), mods_.end(),
                        [&](const InstalledMod& m) { return m.uuid == uuid; });
}

std::string ModManager::installedVersion(const std::string& uuid) const {
    auto it = std::find_if(mods_.begin(), mods_.end(),
                            [&](const InstalledMod& m) { return m.uuid == uuid; });
    return it != mods_.end() ? it->version : std::string();
}

}
