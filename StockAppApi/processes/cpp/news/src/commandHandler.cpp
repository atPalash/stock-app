#include "commandHandler.h"

#include <vector>

#include "googleNewsRss.h"
#include "editConfig.h"
#include "messageParser.h"
#include "logger.h"

namespace News
{
    namespace Src
    {
        CommandHandler::CommandHandler(const std::string &config) : configM(config),
                                                                    commmandsM("headlines, config")
        {
        }

        CommandHandler::~CommandHandler()
        {
        }

        Base::Interface::Response CommandHandler::execute(std::string message)
        {
            try
            {
                auto arguments = Base::Src::parseMessage(message, "--");
                if (arguments["command"] == "headlines")
                {
                    auto news = getNewsInDiscordFormat("intitle:"+arguments["stock"], 10, "30d");
                    return Base::Interface::Response{news, Base::Commons::None,
                                                     "", true};
                }
                else if (arguments["command"] == "config")
                {
                    bool res = edit(arguments["key"], arguments["value"],
                                    arguments["operation"] == "add" ? Base::Src::Operation::Add : Base::Src::Operation::Remove,
                                    configM);
                    
                    return Base::Interface::Response{res ? "success" : "fail", Base::Commons::None,
                                                     "", true};
                }
                else
                {
                    Base::Src::Log::LogError(__FILE__, __LINE__, message);
                    return Base::Interface::Response{"", Base::Commons::MethodNotAllowed,
                                                     "MethodNotAllowed", false};
                }
            }
            catch (const std::exception &e)
            {
                Base::Src::Log::LogCritical(__FILE__, __LINE__, e.what());
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