add_library(silk_core STATIC
    src/GameDetector.cpp
    src/ModManager.cpp
    src/ThunderstoreClient.cpp
    src/ConfigManager.cpp
)

target_include_directories(silk_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(silk_core PUBLIC
    nlohmann_json::nlohmann_json
    miniz
    CURL::libcurl
)

if(BUILD_CLI)
    add_executable(silk_backend_cli src/main.cpp)
    target_link_libraries(silk_backend_cli PRIVATE silk_core)
endif()
