#include "application.h"

#include "headers/logger.h"
#include "headers/server.h"

namespace StockAppApi
{
    namespace application
    {
        Application::Application()
        {

        }

        Application::~Application() {
            
        }

        void Application::Run() {
            StockAppApi::logger::Log::Init();
            StockAppApi::server::Server server{8080};
            server.run();
        }
    }
}
