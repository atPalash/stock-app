#include "commandHandler.h"

#include "boost/format.hpp"

#include "utility/messageParser.h"

namespace DiscordConnector
{
    namespace Src
    {
        CommandHandler::CommandHandler(
            const std::string &token,
            const std::map<std::string, std::string> &webhooks) : tokenM(token),
                                                                  webhooksM(webhooks),
                                                                  discordMessengerM(new Messenger(tokenM))
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

        interfaces::Response CommandHandler::execute(std::string toDoMessage)
        {
            try
            {
                auto content = Utility::parseMessage(toDoMessage, "--");

                if (content["command"] == "sendMessage")
                {
                    discordMessengerM->sendMessage(content["channel"], content["message"]);
                }
                else if (content["command"] == "sendEmbed")
                {
                    discordMessengerM->sendEmbed(content["channel"], content["title"], content["message"]);
                }
                else
                {
                    return interfaces::Response{"", interfaces::ErrorCode::MethodNotAllowed,
                                                std::logic_error("MethodNotAllowed")};
                }
            }
            catch (const std::exception &e)
            {
                std::cerr << e.what() << '\n';
                return interfaces::Response{e.what(), interfaces::ErrorCode::MethodNotAllowed,
                                            std::logic_error("MethodNotAllowed")};
            }
        }
    }
}
