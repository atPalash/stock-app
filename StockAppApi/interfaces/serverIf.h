#pragma once

namespace interfaces
{
    class ServerIf
    {
    public:
        virtual ~ServerIf(){};

        virtual void run() = 0;

        virtual void registerRoutes() = 0;
    };
}
