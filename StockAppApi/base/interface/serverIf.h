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
        };
    }
}
