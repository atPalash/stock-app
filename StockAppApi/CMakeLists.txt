# Define cmake version (MANDOTARY)
cmake_minimum_required(VERSION 3.10) 

# Define cmake version (OPTIONAL, may have CMAKE which initiatest the cmake directory structure e.g. stock-app/CMakeLists.txt)
project(StockAppApi) 

# Define C++ standard version (PREFFERRED)
set(CMAKE_CXX_STANDARD 14) 
# Define C++ standard (PREFFERRED)
set(CMAKE_CXX_STANDARD_REQUIRED ON) 

# Add subdirectory to show in Cmake dir structure. Should add for source file. vendor files are optional.
# add_subdirectory(vendor/Crow) 

# Define all headers and sources to be included in the library.
file(GLOB_RECURSE SOURCES src/sources/*.cpp)
file(GLOB_RECURSE HEADERS src/headers/*.h)

# Create a dynamic/shared library with the source files
add_library(${PROJECT_NAME} SHARED ${HEADERS} ${SOURCES})

# Define which directories this library will expose to outside. let this is target A and B depends on it. check https://leimao.github.io/blog/CMake-Public-Private-Interface/
# PUBLIC	All the objects following PUBLIC will be used for linking to the current target and providing the interface to the other targets that have dependencies on the current target.
# PRIVATE	All the objects following PRIVATE will only be used for linking to the current target.
# INTERFACE	All the objects following INTERFACE will only be used for providing the interface to the other targets that have dependencies on the current target.
target_include_directories(${PROJECT_NAME} PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src/headers)

# Add libs this target depends on
target_link_libraries(${PROJECT_NAME} pthread)