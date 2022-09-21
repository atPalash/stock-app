# Define cmake version (MANDOTARY)
cmake_minimum_required(VERSION 3.10) 

# Define cmake version (OPTIONAL, may have CMAKE which initiatest the cmake directory structure e.g. stock-app/CMakeLists.txt)
project(DiscordConnector) 

# Define C++ standard version (PREFFERRED)
set(CMAKE_CXX_STANDARD 20) 
# Define C++ standard (PREFFERRED)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add DPP as dependency
add_subdirectory(vendor/DPP)

# Define all headers and sources to be included in the library.
file(GLOB_RECURSE SOURCES src/*.cpp)
file(GLOB_RECURSE HEADERS src/*.h)

# Create a dynamic/shared library with the source files
# add_library(${PROJECT_NAME} SHARED ${HEADERS} ${SOURCES})
add_executable(${PROJECT_NAME} ${HEADERS} ${SOURCES})

# Define which directories this library will expose to outside. let this is target A and B depends on it. check https://leimao.github.io/blog/CMake-Public-Private-Interface/
# PUBLIC	All the objects following PUBLIC will be used for linking to the current target and providing the interface to the other targets that have dependencies on the current target.
# PRIVATE	All the objects following PRIVATE will only be used for linking to the current target.
# INTERFACE	All the objects following INTERFACE will only be used for providing the interface to the other targets that have dependencies on the current target.
target_include_directories(${PROJECT_NAME} 
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/vendor/DPP/include
)

# Add libs this target depends on
target_link_libraries(${PROJECT_NAME} pthread Interfaces dpp)