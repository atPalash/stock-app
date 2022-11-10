#include "commandHandler.h"

#include <vector>

#include "googleNewsRss.h"
#include "messageParser.h"

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