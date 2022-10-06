#include <iostream>

#include "src/server.h"

int main()
{
    std::cout << "Hello News!";
    int serverPort = 8082;

    News::Src::Server server{serverPort};
    server.run();

    return 0;
}