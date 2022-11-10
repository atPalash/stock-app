#pragma once

#include "commandHandlerIf.h"

namespace News
{
    namespace Src
    {
        class CommandHandler : public Base::Interface::CommandHandlerIf
        {
        public:
            CommandHandler();
            ~CommandHandler();

            Base::Interface::Response execute(std::string message) override;
            std::string getCommandsAsStr() override;

        private:
            std::string commmandsM;
        };
    }
}