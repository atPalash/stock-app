#include <iostream>

#include "server.h"
#include "logger.h"
#include "src/commandHandler.h"

int main()
{
    std::cout << "Hello StockDataFetcher!";
    int serverPort = 8083;
    int masterServerPort = 8080;
    // Initialize the logger from news server
    std::string selectedStocksYaml{"../../configuration/selected_stocks.yaml"};
    Base::Src::Log::Init("StockDataFetcher");
    auto commandHandler = std::make_unique<StockDataFetcher::Src::CommandHandler>(selectedStocksYaml);
    Base::Src::Server server(serverPort, masterServerPort, std::move(commandHandler));

    std::string masterUrl{"localhost:" + std::to_string(masterServerPort)};     
    return 0;
}