#include "server.h"
#include <regex>
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
              ipAddressM(""),
              commandHandlerM(std::move(commandHandler)) // pass the ownership
        {
            ipAddressM = getIpAddress();
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
                    (boost::format("register --host %1% --port %2% --query %3%") % ipAddressM % portM %
                     commandHandlerM->getCommandsAsStr())
                        .str();
                std::string url{"localhost:8080"};
                if(isRunningInContainer())
                {
                    url = "master:8080"; // master is 8080
                }
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
                    (boost::format("unregister --host %1% --port %2%") % ipAddressM % portM).str();
                
                std::string url{"localhost:8080"};
                if(isRunningInContainer())
                {
                    url = "master:8080"; // master is 8080
                }
                auto res = Base::Src::post(url, registrationMessage);

                Base::Src::Log::LogInfo(__FILE__, __LINE__, registrationMessage);
            }
            catch (const std::exception &e)
            {
                Base::Src::Log::LogCritical(__FILE__, __LINE__, e.what());
            }
        }

        std::string Server::getIpAddress()
        {
            if (ipAddressM == "")
            {
                std::regex inet_regex("inet (\\d+\\.\\d+\\.\\d+\\.\\d+)");
                std::smatch match;
                std::string ifconfig_output;

                // Run the ifconfig command and capture its output
                FILE *pipe = popen("ifconfig", "r");
                if (pipe != nullptr)
                {
                    char buffer[128];
                    while (fgets(buffer, sizeof(buffer), pipe) != nullptr)
                    {
                        ifconfig_output += buffer;
                    }
                    pclose(pipe);
                }

                // Search the output for the first occurrence of "inet " followed by an IP address
                if (std::regex_search(ifconfig_output, match, inet_regex))
                {
                    std::cout << "Your IP address is: " << match[1] << std::endl;
                }
                else
                {
                    std::cerr << "Error: could not find IP address in ifconfig output." << std::endl;
                }

                ipAddressM = match[1];
            }

            return ipAddressM;
        }

        bool Server::isRunningInContainer()
        {
            std::ifstream cgroup_file("/proc/1/cgroup");
            std::string line;
            while (std::getline(cgroup_file, line))
            {
                if (line.find("docker") != std::string::npos || line.find("kube") != std::string::npos)
                {
                    return true;
                }
            }
            return false;
        }
    }
}
