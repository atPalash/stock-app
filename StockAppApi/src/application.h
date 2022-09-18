#pragma once
#include "headers/core.h"

namespace StockAppApi
{
    namespace application
    {
        class Application
        {
        public:
            Application();
            virtual ~Application();
            void Run();
        };
    }
}