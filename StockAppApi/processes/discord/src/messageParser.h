#pragma once

#include <map>

namespace DiscordConnector
{
    /**
     * @brief parse user message to a map of command and arguments. The user
     * should follow this convention <command> <??arg_name> <arg_value>.
     * Note: ?? is needed to parse the arguments properly. Choosing ?? for easier
     * typing in mobile device.
     *
     * @param message to parse
     * @return std::map<std::string, std::string> of commands and arguments. Useful
     * for sending JSON message over http.
     */
    std::map<std::string, std::string> parseMessage(std::string message);
}