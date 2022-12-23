#pragma once

#include <string>
#include "yamlParser.h"

namespace News
{
    namespace Src
    {
        bool edit(const std::string &key, const std::string &value,
                  Base::Src::Operation operation, const std::string& filePath);
    }
}