#pragma once
// install crow to usr/local
#include "crow.h"

#include "serverIf.h"
#include "messenger.h"
#include "commandHandler.h"

namespace DiscordConnector
{
    namespace Src
    {
        class Server : public interfaces::ServerIf
        {
        public:
            Server(int port, const std::string &token, const std::map<std::string, std::string> &webhooks);
            ~Server();

            void run() override;
            void registerRoutes() override{};

        private:
            int portM;
            const std::string &tokenM;
            const std::map<std::string, std::string> &webhooksM;
            std::unique_ptr<Messenger> discordMessengerM;
            std::unique_ptr<CommandHandler> commandHandlerM;
        };
    }
}
