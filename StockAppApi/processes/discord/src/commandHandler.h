#pragma once

#include <string>
#include <map>

namespace DiscordConnector
{
    namespace Src
    {
        enum class ErrorCode
        {
            None,
            NotImplemented,
            Warning,
            Critical
        };

        struct Response
        {
            std::string response;
            ErrorCode errorCode;
            std::exception exception;
        };

        class CommandHandler
        {
        public:
            CommandHandler(){};
            ~CommandHandler(){};

            Response execute(std::string message);
        };
    }
}