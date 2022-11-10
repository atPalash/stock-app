#include "commandHandler.h"

#include <vector>

#include "messageParser.h"
#include "httpRequester.h"
#include "logger.h"

namespace StockAppApi
{
    namespace Src
    {
        CommandHandler::CommandHandler() : commmandsM("register")
        {
        }

        CommandHandler::~CommandHandler()
        {
        }

        Base::Interface::Response CommandHandler::execute(std::string message)
        {
            try
            {
                SA_FILE_INFO(message);
                SA_FILE_FLUSH();
                auto arguments = Base::Src::parseMessage(message, "--");
                if (arguments["command"] == commmandsM)
                {
                    registeredCommands[arguments["query"]] = arguments["port"];
                    return Base::Interface::Response{"registered", Base::Commons::None,
                                                     "", true};
                }
                else if (registeredCommands.find(arguments["command"]) != registeredCommands.end())
                {
                    std::string url = "localhost:" + registeredCommands[arguments["command"]];
                    auto res = Base::Src::post(url, message);
                    return Base::Interface::Response{res.text, Base::Commons::None,
                                                     "", true};
                }
                else
                {
                    return Base::Interface::Response{"", Base::Commons::MethodNotAllowed,
                                                     "MethodNotAllowed", false};
                }
            }
            catch (const std::exception &e)
            {
                return Base::Interface::Response{"exception", Base::Commons::BadRequest,
                                                 e.what(), false};
            }
        }

        std::string CommandHandler::getCommandsAsStr()
        {
            return commmandsM;
        }
    }
}