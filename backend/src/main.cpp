

#include "GameDetector.h"
#include "ModManager.h"
#include "ThunderstoreClient.h"
#include "ConfigManager.h"
#include <iostream>

using namespace silk;

int main(int argc, char** argv) {
    std::string cmd = argc > 1 ? argv[1] : "detect";

    ConfigManager configMgr("./data/config.json");
    AppConfig cfg = configMgr.load();

    if (cmd == "detect") {
        GameDetector detector;
        auto install = detector.detect();
        if (install) {
            std::cout << "找到游戏安装: " << install->path
                      << " (来源: " << install->source << ")\n";
        } else {
            std::cout << "未自动检测到《丝之歌》安装目录，请在设置中手动指定。\n";
        }
        return 0;
    }

    if (cmd == "fetch") {
        ThunderstoreClient client(cfg.community);
        std::cout << "正在从雷霆商店获取模组列表 (community=" << cfg.community << ")...\n";
        auto result = client.fetchPackageList();
        if (!result.success) {
            std::cerr << "错误: " << result.error << "\n";
            return 1;
        }
        std::cout << "共获取到 " << result.packages.size() << " 个模组包\n";
        for (size_t i = 0; i < std::min<size_t>(10, result.packages.size()); ++i) {
            auto& p = result.packages[i];
            std::cout << " - " << p.owner << "/" << p.name
                      << " v" << p.latest.versionNumber
                      << " (下载量: " << p.downloads << ")\n";
        }
        return 0;
    }

    if (cmd == "list") {
        GameDetector detector;
        auto install = detector.detect();
        std::string modsDir = install ? detector.getModsDirectory(*install) : "./Mods";
        ModManager mgr(modsDir, "./data");
        mgr.loadLocalManifest();
        std::cout << "已安装模组数: " << mgr.installedMods().size() << "\n";
        for (auto& m : mgr.installedMods()) {
            std::cout << " - [" << (m.enabled ? "启用" : "禁用") << "] "
                      << m.name << " v" << m.version << " by " << m.author << "\n";
        }
        return 0;
    }

    std::cout << "未知命令: " << cmd << "\n用法: silk_backend_cli detect|list|fetch\n";
    return 1;
}
