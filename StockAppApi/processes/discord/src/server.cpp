#include "server.h"

#include "listener.h"
#include "messenger.h"

namespace DiscordConnector
{
    namespace Src
    {
        Server::Server(int port,
                       const std::string &token,
                       const std::map<std::string, std::string> &webhooks) : portM(port),
                                                                             tokenM(token),
                                                                             webhooksM(webhooks),
                                                                             discordMessengerM(new Messenger(tokenM)),
                                                                             commandHandlerM(new CommandHandler())
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
                try
                {
                    Response res = commandHandlerM->execute(body);
                    switch (res.errorCode)
                    {
                    case ErrorCode::None:
                        return crow::response{200, res.response};
                        break;
                    case ErrorCode::NotImplemented:
                        return crow::response{200, "Method not implemented"};
                        break;
                    case ErrorCode::Critical:
                        return crow::response{200, res.exception.what()};
                        break;
                    default:
                        break;
                    }
                    // this->discordMessengerM->sendEmbed("general", parsedMessage["command"], "got command");
                }
                catch (std::exception& e)
                {
                    return crow::response{400, e.what()};
                }
                catch (...)
                {
                    return crow::response{400};
                }

                return crow::response{400, "undefined exception"}; });

            app.port(portM).multithreaded().run();
        }
    }
}
