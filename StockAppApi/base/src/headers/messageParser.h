#pragma once

#include <string>
#include <map>
#include <vector>

namespace Base
{
    namespace Src
    {
        std::vector<std::string> splitString(const std::string &delimiter, const std::string &textToSplit);

        /**
         * @brief parse user message to a map of command and arguments. The user
         * should follow this convention <command> <--arg_name> <arg_value>.
         * Note: -- is needed to parse the arguments properly. Choosing -- for
         * linux type command line.
         *
         * @param message to parse
         * @param parserSymbol identifier to separate arguments, ?? as mentioned above
         * @return std::map<std::string, std::string> of commands and arguments. Useful
         * for sending JSON message over http.
         */
        std::map<std::string, std::string> parseMessage(const std::string &message, const std::string &parserSymbol);
    }
}