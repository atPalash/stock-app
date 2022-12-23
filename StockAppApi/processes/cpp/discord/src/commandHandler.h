#pragma once

#include "commandHandlerIf.h"

#include "messenger.h"

namespace DiscordConnector
{
    namespace Src
    {
        /**
         * Discord commandHandler.
        */
        class CommandHandler : public Base::Interface::CommandHandlerIf
        {
        public:
            /**
             * @brief Constructor required discord listener bot token, and webhooks which determine where to send the reply.
            */
            CommandHandler(const std::string &token, const std::map<std::string, std::string> &webhooks);
            ~CommandHandler(){};

            /**
             * @ref Base::Interface::CommandHandlerIf
            */
            Base::Interface::Response execute(std::string message) override;

            /**
             * @ref Base::Interface::CommandHandlerIf
            */
            std::string getCommandsAsStr() override;

        private:
            const std::string &tokenM;
            const std::map<std::string, std::string> &webhooksM;
            std::unique_ptr<Messenger> discordMessengerM;
            std::string commmandsM;
        };
    }
}