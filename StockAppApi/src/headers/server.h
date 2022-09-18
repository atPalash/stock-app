#pragma once
// install crow to usr/local
#include "crow.h"

namespace StockAppApi
{
    namespace server
    {
        class Server
        {
            public:
                Server(int port);
                ~Server();

                void run();
            private:
                int portM;
        };
    }
}
