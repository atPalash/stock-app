#pragma once

#include "yaml-cpp/yaml.h"

namespace DiscordConnector
{
    namespace Utility
    {
        /**
         * @brief Read a yaml config file and get the elements
         *
         * @param filePath of file to read
         * @return YAML::Node element map
         */
        YAML::Node parseYaml(std::string filePath);
    }
}
