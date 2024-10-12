cmake_minimum_required(VERSION 3.16)
project(resym)

find_package(LLVM 12 REQUIRED CONFIG)
message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")
include_directories(${LLVM_INCLUDE_DIRS})
add_definitions(${LLVM_DEFINITIONS})
message("${LLVM_LIBRARY_DIRS}")
set(CMAKE_CXX_FLAGS " -g -O0 --std=c++17 ")

include_directories(include)

find_package(Clang REQUIRED CONFIG PATHS "/lib/cmake/clang-12/ClangConfig.cmake")
find_package(nlohmann_json 3.2.0 REQUIRED)
message("${Clang_LIBRARY_DIRS}")

add_definitions(${Clang_DEFINITIONS})

include_directories(
  ${Clang_INCLUDE_DIRS}
)

add_executable(field_access field_access_driver.cc 
utils/compilerUtils.cc 
utils/configUtils.cc
prop_rules/field_access_visitor.cc)
target_link_libraries(field_access clangTooling)
target_link_libraries(field_access protobuf)


message(STATUS "${Clang_LIBRARIES}")
