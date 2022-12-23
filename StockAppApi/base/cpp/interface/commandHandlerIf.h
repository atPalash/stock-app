#pragma once

#include <string>
#include <map>

#include "../../commons/errorCode.h"

namespace Base
{
    namespace Interface
    {
        /**
         * @brief Response object from commandHandler.
         *
         */
        struct Response
        {
            std::string response;
            Commons::HttpErrorCode errorCode;
            std::string exceptionStr;
            bool ok;
        };

        /**
         * @brief Commandhandler interface. The derived classes will implement
         * independent execute methods.
         *
         */
        class CommandHandlerIf
        {
        public:
            virtual ~CommandHandlerIf(){};

            /**
             * @brief Execute the command received in message. The message will
             * be parsed and respective command is to be executed.
             *
             * @param message is of the format <command> --<arg1name> <arg1value>
             * --<arg2name> <arg2value> ...
             * @return Response result of executing the command.
             */
            virtual Response execute(std::string message) = 0;

            /**
             * @brief Get the Commands As comma separated string,
             *
             * @return std::string of all command posssible with this handler.
             */
            virtual std::string getCommandsAsStr() = 0;
        };
    }
}
