#pragma once

#include "commandHandlerIf.h"

#include "messenger.h"

namespace DiscordConnector
{
    namespace Src
    {
        class CommandHandler : public interfaces::CommandHandlerIf
        {
        public:
            CommandHandler(const std::string &token, const std::map<std::string, std::string> &webhooks);
            ~CommandHandler(){};

            interfaces::Response execute(std::string toDoMessage) override;

        private:
            const std::string &tokenM;
            const std::map<std::string, std::string> &webhooksM;
            std::unique_ptr<Messenger> discordMessengerM;
        };
    }
}