#pragma once

#include <string>

#include <cpr/cpr.h>

namespace Base
{
    namespace Src
    {
        void get(std::string url);
        cpr::Response post(std::string url, std::string message);
    }
}