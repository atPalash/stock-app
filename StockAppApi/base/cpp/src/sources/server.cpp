#include "server.h"

#include "boost/format.hpp"
#include "crow.h"

#include "httpRequester.h"
#include "logger.h"

namespace Base
{
    namespace Src
    {
        Server::Server(
            int port,
            int baseServerPort,
            std::unique_ptr<Base::Interface::CommandHandlerIf> commandHandler)
            : portM(port),
              baseServerPortM(baseServerPort),
              commandHandlerM(std::move(commandHandler)) // pass the ownership
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
                        try
                        {
                            auto result = commandHandlerM->execute(req.body);
                            return crow::response{result.errorCode, result.response};
                        }
                        catch (std::exception &e)
                        {
                            Base::Src::Log::LogCritical("POST", __LINE__, e.what());
                            return crow::response{400, e.what()};
                        }
                        catch (...)
                        {
                            Base::Src::Log::LogCritical("POST", __LINE__, "Unknown error");
                            return crow::response{400};
                        } 
                        return crow::response{400, "undefined exception"}; });

            app.port(portM).multithreaded().run();
        }

        void Server::registerRoutes()
        {
            try
            {
                std::string registrationMessage =
                    (boost::format("register --port %1% --query %2%") % portM %
                     commandHandlerM->getCommandsAsStr())
                        .str();
                std::string url{"localhost:8080"};
                auto res = Base::Src::post(url, registrationMessage);

                Base::Src::Log::LogInfo(__FILE__, __LINE__, registrationMessage);
            }
            catch (const std::exception &e)
            {
                Base::Src::Log::LogCritical(__FILE__, __LINE__, e.what());
            }
        }

        void Server::unRegisterRoutes()
        {
            try
            {
                std::string registrationMessage =
                    (boost::format("unregister --port %1%") % portM).str();
                std::string url{"localhost:8080"}; // master is 8080
                auto res = Base::Src::post(url, registrationMessage);

                Base::Src::Log::LogInfo(__FILE__, __LINE__, registrationMessage);
            }
            catch (const std::exception &e)
            {
                Base::Src::Log::LogCritical(__FILE__, __LINE__, e.what());
            }
        }
    }
}
