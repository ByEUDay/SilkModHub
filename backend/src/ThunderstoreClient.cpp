#include "ThunderstoreClient.h"
#include <nlohmann/json.hpp>
#include <curl/curl.h>
#include <algorithm>
#include <cctype>

using json = nlohmann::json;

namespace silk {

namespace {

size_t writeCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    auto* buf = static_cast<std::string*>(userp);
    buf->append(static_cast<char*>(contents), size * nmemb);
    return size * nmemb;
}

int progressCallback(void* clientp, curl_off_t dltotal, curl_off_t dlnow,
                      curl_off_t , curl_off_t ) {
    auto* cb = static_cast<std::function<void(int64_t, int64_t)>*>(clientp);
    if (cb && *cb) {
        (*cb)(static_cast<int64_t>(dlnow), static_cast<int64_t>(dltotal));
    }
    return 0;
}

std::string toLower(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) { return std::tolower(c); });
    return s;
}

}

ThunderstoreClient::ThunderstoreClient(std::string community) : community_(std::move(community)) {}

std::string ThunderstoreClient::apiUrl() const {
    return "https://thunderstore.io/c/" + community_ + "/api/v1/package/";
}

TSResult ThunderstoreClient::fetchPackageList() {
    TSResult result;
    CURL* curl = curl_easy_init();
    if (!curl) {
        result.error = "无法初始化 libcurl";
        return result;
    }

    std::string body;
    std::string url = apiUrl();

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, writeCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &body);
    curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);
    curl_easy_setopt(curl, CURLOPT_ACCEPT_ENCODING, "");
    curl_easy_setopt(curl, CURLOPT_USERAGENT, "SilkModHub/1.0 (+https://github.com/SilkModHub)");

    CURLcode res = curl_easy_perform(curl);


    if (res != CURLE_OK) {
        body.clear();
        res = curl_easy_perform(curl);
    }

    long httpCode = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &httpCode);
    curl_easy_cleanup(curl);

    if (res != CURLE_OK) {
        result.error = std::string("网络请求失败: ") + curl_easy_strerror(res);
        return result;
    }
    if (httpCode != 200) {
        result.error = "雷霆商店返回状态码 " + std::to_string(httpCode) +
                       "（可能该社区尚未开放或名称有误: " + community_ + "）";
        return result;
    }

    return parsePackageJson(body);
}

TSResult ThunderstoreClient::parsePackageJson(const std::string& body) {
    TSResult result;
    try {
        json arr = json::parse(body);
        result.packages.reserve(arr.size());
        for (auto& item : arr) {
            TSPackage pkg;
            pkg.uuid = item.value("full_name", "");
            pkg.name = item.value("name", "");
            pkg.owner = item.value("owner", "");
            pkg.isPinned = item.value("is_pinned", false);
            pkg.isDeprecated = item.value("is_deprecated", false);
            pkg.dateUpdated = item.value("date_updated", "");

            if (item.contains("categories") && item["categories"].is_array()) {
                for (auto& c : item["categories"]) pkg.categories.push_back(c.get<std::string>());
            }

            if (item.contains("versions") && item["versions"].is_array() && !item["versions"].empty()) {
                auto& v = item["versions"][0];
                pkg.description = v.value("description", "");
                pkg.iconUrl = v.value("icon", "");
                pkg.websiteUrl = v.value("website_url", "");
                pkg.downloads = v.value("downloads", 0);

                pkg.latest.versionNumber = v.value("version_number", "");
                pkg.latest.downloadUrl = v.value("download_url", "");
                pkg.latest.description = pkg.description;
                pkg.latest.fileSize = v.value("file_size", 0);

                if (v.contains("dependencies") && v["dependencies"].is_array()) {
                    for (auto& d : v["dependencies"]) pkg.dependencies.push_back(d.get<std::string>());
                }
            }

            if (item.contains("rating_score")) pkg.likes = item.value("rating_score", 0);

            result.packages.push_back(std::move(pkg));
        }
        result.success = true;
    } catch (const std::exception& e) {
        result.error = std::string("解析雷霆商店数据失败: ") + e.what();
    }
    return result;
}

std::vector<TSPackage> ThunderstoreClient::filter(const std::vector<TSPackage>& all,
                                                    const std::string& keyword,
                                                    const std::string& category) {
    std::vector<TSPackage> out;
    std::string kw = toLower(keyword);
    for (auto& p : all) {
        if (!category.empty()) {
            bool hasCat = std::find(p.categories.begin(), p.categories.end(), category) != p.categories.end();
            if (!hasCat) continue;
        }
        if (!kw.empty()) {
            bool match = toLower(p.name).find(kw) != std::string::npos ||
                         toLower(p.owner).find(kw) != std::string::npos ||
                         toLower(p.description).find(kw) != std::string::npos;
            if (!match) continue;
        }
        out.push_back(p);
    }
    return out;
}

bool ThunderstoreClient::downloadFile(const std::string& url, const std::string& destPath,
                                       std::function<void(int64_t, int64_t)> onProgress) {
    CURL* curl = curl_easy_init();
    if (!curl) return false;

    FILE* fp = fopen(destPath.c_str(), "wb");
    if (!fp) {
        curl_easy_cleanup(curl);
        return false;
    }

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, nullptr);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, fp);
    curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 300L);
    curl_easy_setopt(curl, CURLOPT_USERAGENT, "SilkModHub/1.0");

    curl_easy_setopt(curl, CURLOPT_NOPROGRESS, 0L);
    curl_easy_setopt(curl, CURLOPT_XFERINFOFUNCTION, progressCallback);
    curl_easy_setopt(curl, CURLOPT_XFERINFODATA, &onProgress);

    CURLcode res = curl_easy_perform(curl);
    long httpCode = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &httpCode);

    fclose(fp);
    curl_easy_cleanup(curl);

    return res == CURLE_OK && httpCode == 200;
}

}
