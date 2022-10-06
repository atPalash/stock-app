#pragma once

#include <string>

#include <cpr/cpr.h>

namespace DiscordConnector
{
    namespace Utility
    {
        void get(std::string url);
        cpr::Response post(std::string url, std::string message);
        // void post(std::string url, std::map<std::string, std::string> message);
    }
}