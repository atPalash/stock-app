#include "server.h"

#include "googleNewsRss.h"

namespace News
{
    namespace Src
    {
        Server::Server(int port) : portM(port)
        {
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
                    auto res = getNewsInDiscordFormat(body);
                    return crow::response{200, res};
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
