#include "server.h"

#include "listener.h"
#include "messenger.h"
#include "utility/messageParser.h"

namespace DiscordConnector
{
    namespace Src
    {
        Server::Server(int port,
                       const std::string &token,
                       const std::map<std::string, std::string> &webhooks) : portM(port),
                                                                             tokenM(token),
                                                                             webhooksM(webhooks),
                                                                             discordMessengerM(new Messenger(tokenM))
        {
            try
            {
                for (auto const webhook : webhooksM)
                {
                    discordMessengerM->addWebhook(webhook.first, webhook.second);
                }

                // Send a message to first webhook
                discordMessengerM->sendEmbed(webhooks.begin()->first, "server online", "Keep up!");
            }
            catch (const std::exception &e)
            {
                std::cerr << e.what() << std::endl;
                throw;
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
                    parsedMessage = DiscordConnector::Utility::parseMessage(body, "--");
                    this->discordMessengerM->sendEmbed("general", parsedMessage["command"], "got command");
                }
                catch (...)
                {
                    return crow::response(400);
                }

                return crow::response{200, parsedMessage["command"]}; });

            // Start the listener thread
            std::string listenerRouteApi = "http://localhost:" + std::to_string(portM) + "/listener";
            std::thread listenerThread(initListener, listenerRouteApi);

            app.port(portM).multithreaded().run();
        }

        void Server::initListener(const std::string &route)
        {
            DiscordConnector::Src::Listener discordListener{tokenM, route};
        }
    }
}
