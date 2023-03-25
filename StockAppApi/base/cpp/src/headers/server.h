#pragma once

#include <memory>

#include "../../interface/serverIf.h"
#include "../../interface/commandHandlerIf.h"

namespace Base
{
    namespace Src
    {
        class Server : public Base::Interface::ServerIf
        {
        private:
            int portM;
            int baseServerPortM;
            std::string ipAddressM;
            std::unique_ptr<Base::Interface::CommandHandlerIf> commandHandlerM;

        public:
            Server(int port, int baseServerPort,
                   std::unique_ptr<Base::Interface::CommandHandlerIf> commandHandler);
            ~Server();

            virtual void run() override;
            virtual void registerRoutes() override;
            virtual void unRegisterRoutes() override;
            virtual std::string getIpAddress() override;
        
        private:
            bool isRunningInContainer();
        };
    }
}