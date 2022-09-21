#pragma once
// install crow to usr/local
#include "crow.h"

#include "serverIf.h"

namespace StockAppApi
{
    namespace server
    {
        class Server : public interfaces::ServerIf
        {
            public:
                Server(int port);
                ~Server();

                void run() override;
                void registerRoutes() override {};
            private:
                int portM;
        };
    }
}
