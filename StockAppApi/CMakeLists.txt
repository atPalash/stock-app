# Define cmake version (MANDOTARY)
cmake_minimum_required(VERSION 3.10) 

# Define cmake version (OPTIONAL, may have CMAKE which initiatest the cmake directory structure e.g. stock-app/CMakeLists.txt)
project(StockAppApi) 

# Define C++ standard version (PREFFERRED)
set(CMAKE_CXX_STANDARD 20) 
# Define C++ standard (PREFFERRED)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add subdirectory to show in Cmake dir structure. Should add for source file. vendor files are optional.
add_subdirectory(vendor/Crow)
add_subdirectory(vendor/cpr)
add_subdirectory(vendor/DPP)
add_subdirectory(vendor/json)
add_subdirectory(vendor/pugixml)
add_subdirectory(vendor/spdlog)
add_subdirectory(vendor/yaml-cpp)

add_subdirectory(base)
add_subdirectory(processes/master)
add_subdirectory(processes/news)
add_subdirectory(processes/discord)