#pragma once

#include <mutex> 

#include "yaml-cpp/yaml.h"

namespace Base
{
    namespace Src
    {
        enum Operation
        {
            Add = 0, 
            Remove
        };

        /**
         * @brief Read a yaml config file and get the elements
         *
         * @param filePath of file to read
         * @return YAML::Node element map
         */
        YAML::Node parseYaml(std::string filePath);

        void editYaml(const std::string &key, const std::string &value, 
        Operation operation, const std::string &filepath);
        
    }
}
