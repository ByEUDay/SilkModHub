#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>

#include "GameDetector.h"
#include "ModManager.h"
#include "ThunderstoreClient.h"
#include "ConfigManager.h"

namespace py = pybind11;
using namespace silk;

PYBIND11_MODULE(silk_backend, m) {
    m.doc() = "SilkModHub C++ 后端 - 通过 pybind11 暴露给 PyQt6 前端";


    py::class_<GameInstall>(m, "GameInstall")
        .def(py::init<>())
        .def_readwrite("path", &GameInstall::path)
        .def_readwrite("executable", &GameInstall::executable)
        .def_readwrite("source", &GameInstall::source)
        .def_readwrite("valid", &GameInstall::valid);

    py::class_<GameDetector>(m, "GameDetector")
        .def(py::init<>())
        .def("detect", &GameDetector::detect)
        .def("validate_manual_path", &GameDetector::validateManualPath)
        .def("get_mods_directory", &GameDetector::getModsDirectory)
        .def("get_loader_directory", &GameDetector::getLoaderDirectory);


    py::class_<InstalledMod>(m, "InstalledMod")
        .def(py::init<>())
        .def_readwrite("uuid", &InstalledMod::uuid)
        .def_readwrite("name", &InstalledMod::name)
        .def_readwrite("author", &InstalledMod::author)
        .def_readwrite("version", &InstalledMod::version)
        .def_readwrite("description", &InstalledMod::description)
        .def_readwrite("install_path", &InstalledMod::installPath)
        .def_readwrite("enabled", &InstalledMod::enabled)
        .def_readwrite("is_dependency_only", &InstalledMod::isDependencyOnly);

    py::class_<ModManager>(m, "ModManager")
        .def(py::init<std::string, std::string>(), py::arg("game_mods_dir"), py::arg("data_dir"))
        .def("load_local_manifest", &ModManager::loadLocalManifest)
        .def("save_local_manifest", &ModManager::saveLocalManifest)
        .def("installed_mods", &ModManager::installedMods, py::return_value_policy::reference_internal)
        .def("install_from_zip", &ModManager::installFromZip,
             py::arg("zip_path"), py::arg("uuid"), py::arg("name"),
             py::arg("author"), py::arg("version"), py::arg("description"),
             py::arg("on_progress") = nullptr,
             py::call_guard<py::gil_scoped_release>())
        .def("uninstall", &ModManager::uninstall)
        .def("set_enabled", &ModManager::setEnabled)
        .def("is_installed", &ModManager::isInstalled)
        .def("installed_version", &ModManager::installedVersion);


    py::class_<TSVersion>(m, "TSVersion")
        .def(py::init<>())
        .def_readwrite("version_number", &TSVersion::versionNumber)
        .def_readwrite("download_url", &TSVersion::downloadUrl)
        .def_readwrite("description", &TSVersion::description)
        .def_readwrite("file_size", &TSVersion::fileSize);

    py::class_<TSPackage>(m, "TSPackage")
        .def(py::init<>())
        .def_readwrite("uuid", &TSPackage::uuid)
        .def_readwrite("name", &TSPackage::name)
        .def_readwrite("owner", &TSPackage::owner)
        .def_readwrite("description", &TSPackage::description)
        .def_readwrite("icon_url", &TSPackage::iconUrl)
        .def_readwrite("website_url", &TSPackage::websiteUrl)
        .def_readwrite("categories", &TSPackage::categories)
        .def_readwrite("dependencies", &TSPackage::dependencies)
        .def_readwrite("downloads", &TSPackage::downloads)
        .def_readwrite("likes", &TSPackage::likes)
        .def_readwrite("is_pinned", &TSPackage::isPinned)
        .def_readwrite("is_deprecated", &TSPackage::isDeprecated)
        .def_readwrite("date_updated", &TSPackage::dateUpdated)
        .def_readwrite("latest", &TSPackage::latest);

    py::class_<TSResult>(m, "TSResult")
        .def(py::init<>())
        .def_readwrite("success", &TSResult::success)
        .def_readwrite("error", &TSResult::error)
        .def_readwrite("packages", &TSResult::packages);

    py::class_<ThunderstoreClient>(m, "ThunderstoreClient")
        .def(py::init<std::string>(), py::arg("community") = "silksong")
        .def("set_community", &ThunderstoreClient::setCommunity)
        .def("community", &ThunderstoreClient::community)
        .def("fetch_package_list", &ThunderstoreClient::fetchPackageList,
             py::call_guard<py::gil_scoped_release>())
        .def_static("filter", &ThunderstoreClient::filter,
                    py::arg("all"), py::arg("keyword"), py::arg("category") = "")
        .def("download_file", &ThunderstoreClient::downloadFile,
             py::arg("url"), py::arg("dest_path"), py::arg("on_progress") = nullptr,
             py::call_guard<py::gil_scoped_release>());


    py::class_<AppConfig>(m, "AppConfig")
        .def(py::init<>())
        .def_readwrite("game_path", &AppConfig::gamePath)
        .def_readwrite("theme", &AppConfig::theme)
        .def_readwrite("community", &AppConfig::community)
        .def_readwrite("check_updates_on_start", &AppConfig::checkUpdatesOnStart)
        .def_readwrite("language", &AppConfig::language);

    py::class_<ConfigManager>(m, "ConfigManager")
        .def(py::init<std::string>())
        .def("load", &ConfigManager::load)
        .def("save", &ConfigManager::save)
        .def("path", &ConfigManager::path);
}
