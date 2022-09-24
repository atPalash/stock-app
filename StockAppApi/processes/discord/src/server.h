#pragma once
// install crow to usr/local
#include "crow.h"

#include "serverIf.h"
#include "messenger.h"

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
            /**
             * @brief Runs the listener in a separate thread.
             *
             * @param route api address to post messages from listener.e.g. errors
             */
            void initListener(const std::string &route);

        private:
            int portM;
            const std::string &tokenM;
            const std::map<std::string, std::string> &webhooksM;
            std::unique_ptr<Messenger> discordMessengerM;
        };
    }
}
