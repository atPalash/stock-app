#include "commandHandler.h"

#include "boost/format.hpp"

#include "messageParser.h"
#include "logger.h"

namespace DiscordConnector
{
    namespace Src
    {
        CommandHandler::CommandHandler(
            const std::string &token,
            const std::map<std::string, std::string> &webhooks) : tokenM(token),
                                                                  webhooksM(webhooks),
                                                                  discordMessengerM(new Messenger(tokenM)),
                                                                  commmandsM("sendMessage, sendEmbed")
        {
            try
            {
                for (auto const webhook : webhooksM)
                {
                    discordMessengerM->addWebhook(webhook.first, webhook.second);
                }

                // Send a message to general webhook
                discordMessengerM->sendEmbed("general", "server online", "Keep up!");
            }
            catch (const std::exception &e)
            {
                Base::Src::Log::LogCritical(__FILE__, __LINE__, e.what());
                throw;
            }
        }

        Base::Interface::Response CommandHandler::execute(std::string message)
        {
            try
            {
                auto content = Base::Src::parseMessage(message, "--");

                if (content["command"] == "sendMessage")
                {
                    discordMessengerM->sendMessage(content["channel"], content["message"]);
                }
                else if (content["command"] == "sendEmbed")
                {
                    discordMessengerM->sendEmbed(content["channel"], content["title"], content["message"]);
                }

                return Base::Interface::Response{content["message"], Base::Commons::None,
                                                 "", true};
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
