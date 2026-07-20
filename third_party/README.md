# 本地预下载依赖说明

CMake 配置时默认会通过 `FetchContent` 从 GitHub 拉取以下三个依赖库源码。
如果你的网络访问 GitHub 很慢或不通，会导致 `cmake ..` 卡在
`-- Detecting CXX compile features - done` 之后不动（其实是在后台等 git clone）。

现在 `CMakeLists.txt` 已经改成：**优先检测本项目下 `third_party/<name>/` 目录里
有没有对应源码，有就直接用本地的，完全不走网络；没有才会回退去 GitHub 拉取。**

只需按下面步骤，把三个库的源码手动下载好放进对应目录即可。

## 需要下载的三个库

| 目录 | 库 | 版本 tag | 下载地址（zip 源码包） |
|---|---|---|---|
| `third_party/json` | nlohmann/json | v3.11.3 | https://github.com/nlohmann/json/archive/refs/tags/v3.11.3.zip |
| `third_party/miniz` | miniz | 3.0.2 | https://github.com/richgel999/miniz/archive/refs/tags/3.0.2.zip |
| `third_party/pybind11` | pybind11 | v2.13.6 | https://github.com/pybind/pybind11/archive/refs/tags/v2.13.6.zip |

> 如果 GitHub 打不开，也可以在国内镜像站（如 gitee 的镜像仓库、或
> https://ghproxy.com/ 等加速代理）搜索同名同版本的源码包下载，内容是一样的。

## 放置方法

下载的 zip 解压后，通常会得到一个类似 `json-3.11.3/`、`miniz-3.0.2/`、
`pybind11-2.13.6/` 的顶层文件夹。**要把这个文件夹里面的内容直接放到对应的
`third_party/<name>/` 目录下**（不要多一层嵌套），确保能看到：

```
third_party/json/CMakeLists.txt
third_party/json/include/nlohmann/json.hpp
...

third_party/miniz/CMakeLists.txt
third_party/miniz/miniz.c
...

third_party/pybind11/CMakeLists.txt
third_party/pybind11/include/pybind11/pybind11.h
...
```

判断标准很简单：`third_party/<name>/` 下面能直接看到一个 `CMakeLists.txt`
文件，就算放对了（CMake 也是靠检测这个文件来判断"本地有没有源码"的）。

## 命令行下载参考（如果你机器能连 GitHub，只是嫌它拉全部历史慢）

```bash
cd third_party

curl -L -o json.zip    https://github.com/nlohmann/json/archive/refs/tags/v3.11.3.zip
unzip json.zip && rm -rf json && mv json-3.11.3 json && rm json.zip

curl -L -o miniz.zip   https://github.com/richgel999/miniz/archive/refs/tags/3.0.2.zip
unzip miniz.zip && rm -rf miniz && mv miniz-3.0.2 miniz && rm miniz.zip

curl -L -o pybind11.zip https://github.com/pybind/pybind11/archive/refs/tags/v2.13.6.zip
unzip pybind11.zip && rm -rf pybind11 && mv pybind11-2.13.6 pybind11 && rm pybind11.zip
```

放好之后重新执行：

```bash
rm -rf build
mkdir build && cd build
cmake ..
```

终端应该会打印类似：

```
-- [json] 使用本地预下载源码: /path/to/SilkModHub/third_party/json
-- [miniz] 使用本地预下载源码: /path/to/SilkModHub/third_party/miniz
-- [pybind11] 使用本地预下载源码: /path/to/SilkModHub/third_party/pybind11
```

不再有任何 git clone 网络请求，也就不会再卡住了。

## 另外注意

`find_package(CURL REQUIRED)` 用的是系统自带的 libcurl，不走网络下载，
需要你本机装好开发库，例如：

- Ubuntu/Debian: `sudo apt install libcurl4-openssl-dev`
- macOS (Homebrew): `brew install curl`
- Windows: 建议用 vcpkg 安装 `curl`，再在 cmake 命令加上
  `-DCMAKE_TOOLCHAIN_FILE=<vcpkg路径>/scripts/buildsystems/vcpkg.cmake`
