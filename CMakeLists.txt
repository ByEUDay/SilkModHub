cmake_minimum_required(VERSION 3.16)
project(SilkModHub LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

option(BUILD_PYTHON_BINDINGS "构建 pybind11 Python 绑定 (silk_backend 模块)" ON)
option(BUILD_CLI "构建独立命令行测试可执行文件" ON)

include(FetchContent)

# 本地预下载依赖存放目录：third_party/<name>/
# 若该目录存在且含 CMakeLists.txt，则直接使用本地源码，不再走网络 git clone；
# 否则回退到从 GitHub 拉取（需要网络）。
set(THIRD_PARTY_DIR "${CMAKE_SOURCE_DIR}/third_party")

function(sh_declare_dep name git_repo git_tag)
    set(local_dir "${THIRD_PARTY_DIR}/${name}")
    if(EXISTS "${local_dir}/CMakeLists.txt")
        message(STATUS "[${name}] 使用本地预下载源码: ${local_dir}")
        FetchContent_Declare(${name} SOURCE_DIR "${local_dir}")
    else()
        message(STATUS "[${name}] 未找到本地源码 (${local_dir})，将从 ${git_repo} 拉取")
        FetchContent_Declare(${name} GIT_REPOSITORY ${git_repo} GIT_TAG ${git_tag})
    endif()
endfunction()

# ---- nlohmann/json ----
sh_declare_dep(json https://github.com/nlohmann/json.git v3.11.3)
# ---- miniz（零依赖的 zip 解压库） ----
sh_declare_dep(miniz https://github.com/richgel999/miniz.git 3.0.2)

FetchContent_MakeAvailable(json miniz)

find_package(CURL REQUIRED)

add_subdirectory(backend)

if(BUILD_PYTHON_BINDINGS)
    sh_declare_dep(pybind11 https://github.com/pybind/pybind11.git v2.13.6)
    FetchContent_MakeAvailable(pybind11)
    add_subdirectory(bindings)
endif()
