#include <iostream>

#include "src/server.h"
#include "utility/yamlParser.h"

int main()
{
    std::cout << "Hello Discord!";

    /* Setup the bot */
    YAML::Node config = DiscordConnector::Utility::parseYaml("config.yaml");
    std::string token = config["listener"]["bot"]["token"].as<std::string>();

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