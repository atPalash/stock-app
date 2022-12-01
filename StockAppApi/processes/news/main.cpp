#include <iostream>

#include "server.h"
#include "logger.h"
#include "src/commandHandler.h"

int main()
{
    std::cout << "Hello News!";
    int serverPort = 8082;
    int masterServerPort = 8080;
    // Initialize the logger from news server
    Base::Src::Log::Init("News");
    auto commandHandler = std::make_unique<News::Src::CommandHandler>();
    Base::Src::Server server(serverPort, masterServerPort, std::move(commandHandler));
    server.registerRoutes();
    server.run();
    server.unRegisterRoutes();

    return 0;
}