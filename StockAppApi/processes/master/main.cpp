#include <iostream>

#include "server.h"
#include "src/commandHandler.h"

int main()
{
    std::cout << "Hello StockAppApi!";
    int serverPort = 8080;
    int masterServerPort = -1;

    auto commandHandler = std::make_unique<StockAppApi::Src::CommandHandler>();
    Base::Src::Server server(serverPort, masterServerPort, std::move(commandHandler));
    server.run();

    return 0;
}