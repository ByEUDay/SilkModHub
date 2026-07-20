#pragma once
#include <string>
#include <vector>
#include <cstdint>
#include <functional>

namespace silk {


struct TSVersion {
    std::string versionNumber;
    std::string downloadUrl;
    std::string description;
    int64_t fileSize = 0;
};


struct TSPackage {
    std::string uuid;
    std::string name;
    std::string owner;
    std::string description;
    std::string iconUrl;
    std::string websiteUrl;
    std::vector<std::string> categories;
    std::vector<std::string> dependencies;
    int64_t downloads = 0;
    int64_t likes = 0;
    bool isPinned = false;
    bool isDeprecated = false;
    std::string dateUpdated;
    TSVersion latest;
};


struct TSResult {
    bool success = false;
    std::string error;
    std::vector<TSPackage> packages;
};


class ThunderstoreClient {
public:

    explicit ThunderstoreClient(std::string community = "silksong");

    void setCommunity(const std::string& community) { community_ = community; }
    const std::string& community() const { return community_; }


    TSResult fetchPackageList();


    static std::vector<TSPackage> filter(const std::vector<TSPackage>& all,
                                          const std::string& keyword,
                                          const std::string& category = "");


    bool downloadFile(const std::string& url, const std::string& destPath,
                       std::function<void(int64_t, int64_t)> onProgress = nullptr);

private:
    std::string community_;
    std::string apiUrl() const;
    TSResult parsePackageJson(const std::string& body);
};

}
