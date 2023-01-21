#include "yamlParser.h"

#include <fstream>
#include <iostream>
#include <unistd.h>

namespace Base
{
    namespace Src
    {
        std::mutex fileLock;
        YAML::Node parseYaml(std::string filePath)
        {
            while (!fileLock.try_lock())
            {
                sleep(1);
            }

            try
            {
                YAML::Node config = YAML::LoadFile(filePath);
                fileLock.unlock();
                return config;
            }
            catch (const std::exception &e)
            {
                fileLock.unlock();
                throw;
            }
        }

        void editYaml(const std::string &key, const std::string &value, Operation operation, const std::string &filepath)
        {
            YAML::Node yaml = parseYaml(filepath);
            try
            {
                auto check = yaml[key];
                auto removeValueIfPresent = [&]() 
                {
                    for (int i = 0; i < check.size(); i++)
                    {
                        if (check[i].as<std::string>() == value)
                        {
                            yaml[key].remove(i);
                            break;
                        }
                    }
                };
                if (operation == Operation::Add)
                {
                    removeValueIfPresent();
                    yaml[key].push_back(value);
                }
                else if (operation == Operation::Remove)
                {
                    removeValueIfPresent();
                }
                else
                {
                    throw std::invalid_argument("This edit operation is not allowed");
                }

                yaml[key].reset();
                while (!fileLock.try_lock())
                {
                    sleep(1);
                }
                std::ofstream fout(filepath);
                fout << yaml;
                fileLock.unlock();
            }
            catch (const std::runtime_error &error)
            {
                throw;
            }
        }
    }
}
