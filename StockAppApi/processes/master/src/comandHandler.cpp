#include "commandHandler.h"

#include <vector>

#include <boost/algorithm/string.hpp>

#include "messageParser.h"
#include "httpRequester.h"
#include "logger.h"

namespace StockAppApi
{
    namespace Src
    {
        CommandHandler::CommandHandler() : commmandsM("register, unregister")
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
                if (arguments["command"] == "register")
                {
                    std::vector<std::string> commandsArr;
                    boost::split(commandsArr, arguments["query"], boost::is_any_of(","));

                    for (auto query : commandsArr)
                    {
                        boost::trim(query); // trim spaces
                        registeredCommands[query] = arguments["port"];
                    }
                    return Base::Interface::Response{"registered", Base::Commons::None,
                                                     "", true};
                }
                else if (arguments["command"] == "unregister")
                {
                    for (auto command : registeredCommands)
                    {
                        if (command.second == arguments["port"])
                        {
                            registeredCommands.erase(command.first);
                        }
                    }
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
                    return Base::Interface::Response{"MethodNotAllowed", Base::Commons::MethodNotAllowed,
                                                     "", false};
                }
            }
            catch (const std::exception &e)
            {
                return Base::Interface::Response{"exception", Base::Commons::BadRequest,
                                                 e.what(), false};
            }

            return Base::Interface::Response{"NoContent", Base::Commons::NoContent,
                                             "", false};
        }

        std::string CommandHandler::getCommandsAsStr()
        {
            return commmandsM;
        }
    }
}