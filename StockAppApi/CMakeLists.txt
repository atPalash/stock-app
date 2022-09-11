cmake_minimum_required(VERSION 3.10)

project(StockAppApi)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_subdirectory(vendor/Crow)

add_library(${PROJECT_NAME} SHARED
src/server/server.h
src/server/server.cpp)

target_include_directories(${PROJECT_NAME} PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src/server)
target_link_libraries(${PROJECT_NAME} pthread)