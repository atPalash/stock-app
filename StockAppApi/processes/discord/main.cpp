#include <iostream>

#include "src/listener.h"
#include "src/server.h"
#include "utility/yamlParser.h"

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
    std::cout << "Hello Discord!";
    int serverPort = 8081;
    // Setup the bot
    YAML::Node config = DiscordConnector::Utility::parseYaml("config.yaml");
    std::string token = config["listener"]["bot"]["token"].as<std::string>();

    // Start the listener
    std::string api = "http://localhost:" + std::to_string(serverPort) + "/";
    std::thread listenerThread(initListener, token, api);

    /* Get the messenger webhooks */
    std::map<std::string, std::string> webhooks;
    for (auto webhook : config["messenger"]["webhook"])
    {
        webhooks.insert({webhook.first.as<std::string>(), webhook.second.as<std::string>()});
    }

    DiscordConnector::Src::Server server{8081, token, webhooks};
    server.run();

    listenerThread.join();
    return 0;
}