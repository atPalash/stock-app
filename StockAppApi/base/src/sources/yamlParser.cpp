#include "yamlParser.h"

#include <iostream>

namespace Base
{
    namespace Src
    {
        YAML::Node parseYaml(std::string filePath)
        {
            try
            {
                YAML::Node config = YAML::LoadFile("config.yaml");
                return config;
            }
            catch (const std::exception &e)
            {
                throw;
            }
        }
    }
}
