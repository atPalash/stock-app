#include "application.h"

#include <iostream>
int main()
{
    std::cout << "Hello World!";
    StockAppApi::application::Application stockAppApi{};
    stockAppApi.Run();
    return 0; 
}