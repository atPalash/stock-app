#include "commandHandler.h"

#include <vector>

#include "googleNewsRss.h"
#include "messageParser.h"
#include "logger.h"

namespace News
{
    namespace Src
    {
        CommandHandler::CommandHandler() : commmandsM("headlines")
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
                if (arguments["command"] == commmandsM)
                {
                    auto news = getNewsInDiscordFormat(arguments["stock"]);
                    return Base::Interface::Response{news, Base::Commons::None,
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