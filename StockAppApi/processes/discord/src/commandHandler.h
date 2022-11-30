#pragma once

#include "commandHandlerIf.h"

#include "messenger.h"

namespace DiscordConnector
{
    namespace Src
    {
        class CommandHandler : public Base::Interface::CommandHandlerIf
        {
        public:
            CommandHandler(const std::string &token, const std::map<std::string, std::string> &webhooks);
            ~CommandHandler(){};

            Base::Interface::Response execute(std::string message) override;
            std::string getCommandsAsStr() override;

        private:
            const std::string &tokenM;
            const std::map<std::string, std::string> &webhooksM;
            std::unique_ptr<Messenger> discordMessengerM;
            std::string commmandsM;
        };
    }
}