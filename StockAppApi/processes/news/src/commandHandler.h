#pragma once

#include "commandHandlerIf.h"

namespace News
{
    namespace Src
    {
        /**
         * Discord commandHandler.
        */
        class CommandHandler : public Base::Interface::CommandHandlerIf
        {
        public:
            CommandHandler();
            ~CommandHandler();

            /**
             * @ref Base::Interface::CommandHandlerIf
            */
            Base::Interface::Response execute(std::string message) override;

            /**
             * @ref Base::Interface::CommandHandlerIf
            */
            std::string getCommandsAsStr() override;

        private:
            std::string commmandsM;
        };
    }
}