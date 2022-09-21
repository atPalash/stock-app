#include "server.h"

#include "messenger.h"
#include "messageParser.h"

namespace DiscordConnector
{
    Server::Server(int port, std::string &token) : portM(port),
                                                   tokenM(token),
                                                   discordMessengerM(new Messenger(tokenM))
    {
        try
        {
            std::string wh{"https://discord.com/api/webhooks/961329477785387008/yAYntyDBdRLX56vi78BlSNAgf64ZQ_Ae5ekJzOc0f93XAGV5pQ0U016VBrV3gaLF5FPm"};
            discordMessengerM->addWebhook("querry", wh);
        }
        catch (const std::exception &e)
        {
            std::cerr << e.what() << '\n';
        }
    }

    Server::~Server()
    {
    }

    void Server::run()
    {
        crow::SimpleApp app;

        CROW_ROUTE(app, "/")
            .methods("POST"_method)([this](const crow::request &req)
                                    {
                auto body = req.body;
                
                std::map<std::string, std::string> parsedMessage;
                try
                {
                    parsedMessage = DiscordConnector::parseMessage(body);
                    this->discordMessengerM->sendMessage("general", parsedMessage["command"]);
                    this->discordMessengerM->sendEmbed("general", parsedMessage["command"], "got command");
                }
                catch (...)
                {
                    return crow::response(400);
                }

                return crow::response{200, parsedMessage["command"]}; });

        app.port(portM).multithreaded().run();
    }
}
