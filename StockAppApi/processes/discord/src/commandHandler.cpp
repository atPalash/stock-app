#include "commandHandler.h"

#include "boost/format.hpp"

#include "messageParser.h"

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

                // Send a message to first webhook
                discordMessengerM->sendEmbed(webhooks.begin()->first, "server online", "Keep up!");
            }
            catch (const std::exception &e)
            {
                std::cerr << e.what() << std::endl;
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
