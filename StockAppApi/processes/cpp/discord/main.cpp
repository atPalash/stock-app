#include <iostream>

#include "src/listener.h"
#include "server.h"
#include "logger.h"
#include "yamlParser.h"
#include "src/commandHandler.h"

/**
 * @brief Runs the listener in a separate thread.
 *
 * @param token bot token
 * @param route api address to post messages from listener.e.g. errors
 */
void initListener(const std::string token, const std::string &route)
{
    DiscordConnector::Src::Listener discordListener{token, route};
}

int main()
{
    std::cout << "Hello Discord!" << std::endl;

    std::string configFolder = "configuration/";
    YAML::Node config = Base::Src::parseYaml(get_app_path('config.yaml'));
    int serverPort = config["port"]["discord"].as<int>();
    int masterServerPort =  config["port"]["master"].as<int>();

    // Initialize the logger from master server
    Base::Src::Log::Init("Discord");

    // Setup the bot
    std::string token = config["listener"]["bot"]["token"].as<std::string>();

    // Start the listener
    std::string api = "http://localhost:" + std::to_string(masterServerPort) + "/";
    std::thread listenerThread(initListener, token, api);

    /* Get the messenger webhooks */
    std::map<std::string, std::string> webhooks;
    for (auto webhook : config["messenger"]["webhook"])
    {
        webhooks.insert({webhook.first.as<std::string>(), webhook.second.as<std::string>()});
    }

    auto commandHandler = std::make_unique<DiscordConnector::Src::CommandHandler>(token, webhooks);
    Base::Src::Server server(serverPort, masterServerPort, std::move(commandHandler));
    server.registerRoutes();
    server.run();
    server.unRegisterRoutes();

    listenerThread.join();
    return 0;
}
