#pragma once
// install crow to usr/local
#include "crow.h"

#include "serverIf.h"
#include "messenger.h"

namespace DiscordConnector
{
    class Server : public interfaces::ServerIf
    {
    public:
        Server(int port);
        Server(int port, std::string &token);
        ~Server();

        void run() override;
        void registerRoutes() override{};

    private:
        int portM;
        std::string tokenM;
        std::unique_ptr<Messenger> discordMessengerM;
    };
}
