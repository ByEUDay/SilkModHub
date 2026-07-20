pybind11_add_module(silk_backend bindings.cpp)
target_link_libraries(silk_backend PRIVATE silk_core)

# 将编译好的模块直接输出到 frontend 目录，方便 Python 端 import
set_target_properties(silk_backend PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/frontend
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/frontend
)
