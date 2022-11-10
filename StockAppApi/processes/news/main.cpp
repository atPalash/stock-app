#include <iostream>

#include "server.h"
#include "src/commandHandler.h"

int main()
{
    std::cout << "Hello News!";
    int serverPort = 8082;
    int masterServerPort = 8080;

    auto commandHandler = std::make_unique<News::Src::CommandHandler>();
    Base::Src::Server server(serverPort, masterServerPort, std::move(commandHandler));
    server.registerRoutes();
    server.run();

    return 0;
}