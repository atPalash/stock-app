#pragma once
// install crow to usr/local
#include "crow.h"

#include "serverIf.h"

namespace News
{
    namespace Src
    {
        class Server : public interfaces::ServerIf
        {
        public:
            Server(int port);
            ~Server();

            void run() override;
            void registerRoutes() override{};

        private:
            int portM;
        };
    }
}
