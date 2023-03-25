#pragma once

namespace Base
{
    namespace Interface
    {
        class ServerIf
        {
        public:
            virtual ~ServerIf(){};

            /**
             * @brief Start the server.
             *
             */
            virtual void run() = 0;

            /**
             * @brief Register this server to the master server.
             *
             */
            virtual void registerRoutes() = 0;

            /**
             * @brief Unregister the routes when client server goes off.
             *
             */
            virtual void unRegisterRoutes() = 0;

            /**
             * @brief Get Ip address of the host running this server
             *
             */
            virtual std::string getIpAddress() = 0;
        };
    }
}
