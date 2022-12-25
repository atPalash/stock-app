#include <iostream>

#include "server.h"
#include "src/commandHandler.h"
#include "logger.h"
#include "yamlParser.h"

int main()
{
    std::cout << "Hello StockAppApi!";

    std::string configFolder = "../../../configuration/";
    YAML::Node config = Base::Src::parseYaml(configFolder + "config.yaml");
    int serverPort = config["port"]["master"].as<int>();
    int masterServerPort = -1; // This is master server

    // Initialize the logger from master server
    Base::Src::Log::Init("StockAppApi");

    auto commandHandler = std::make_unique<StockAppApi::Src::CommandHandler>();
    Base::Src::Server server(serverPort, masterServerPort, std::move(commandHandler));
    server.run();

    return 0;
}