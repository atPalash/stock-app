#include <iostream>

#include "server.h"
#include "logger.h"
#include "src/commandHandler.h"
#include "src/googleNewsListener.h"
#include "yamlParser.h"

/**
 * @brief Runs the news listener in a separate thread.
 *
 * @param stockListYaml selected stock list
 * @param interval polling in minutes
 * @param masterUrl to post result
 */
void runListener(News::Src::GoogleNewsListener& listener)
{
    try
    {
        listener.run();    
    }
    catch(const std::exception& e)
    {
        Base::Src::Log::LogCritical(__FILE__, __LINE__, e.what());
    }
}

void stopListener(News::Src::GoogleNewsListener& listener)
{
    listener.stop();
}

int main()
{
    std::cout << "Hello News!";

    std::string configFolder = "configuration/";
    YAML::Node config = Base::Src::parseYaml(configFolder + "config.yaml");
    int serverPort = config["port"]["news"].as<int>();
    int masterServerPort =  config["port"]["master"].as<int>();

    // Initialize the logger from news server
    std::string selectedStocksYaml{configFolder + "selected_stocks.yaml"};
    Base::Src::Log::Init("News");
    auto commandHandler = std::make_unique<News::Src::CommandHandler>(selectedStocksYaml);
    Base::Src::Server server(serverPort, masterServerPort, std::move(commandHandler));

    std::string masterUrl{"localhost:" + std::to_string(masterServerPort)}; 
    News::Src::GoogleNewsListener listener(selectedStocksYaml, 60, masterUrl);
    std::thread listenerThread(runListener, std::ref(listener));

    server.registerRoutes();
    server.run();
    server.unRegisterRoutes();

    stopListener(listener);

    listenerThread.join();
    
    return 0;
}