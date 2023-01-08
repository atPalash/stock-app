#include "messenger.h"
#include "utility/embed.h"

namespace DiscordConnector
{
    namespace Src
    {
        Messenger::Messenger(const std::string &token) : tokenM(token),
                                                         botM(new dpp::cluster(tokenM, dpp::i_default_intents | dpp::i_message_content))
        {
        }

        Messenger::Messenger() : tokenM(""),
                                 botM(new dpp::cluster("", dpp::i_default_intents | dpp::i_message_content))
        {
        }
        Messenger::~Messenger()
        {
            botM->shutdown();
        }

        void Messenger::sendEmbed(const std::string &channel, const std::string &title, const std::string &message) const
        {
            auto itr = channelWebhookM.find(channel);
            if (itr != channelWebhookM.end())
            {
                std::vector<std::string> chunks = Utility::divideInChunks(message);
                for (auto &chunk : chunks)
                {
                    /* create the embed */
                    dpp::embed embed = dpp::embed()
                                           .set_color(dpp::colors::sti_blue)
                                           .set_description(chunk)
                                           .set_timestamp(time(0));
                    /* reply with the created embed */
                    botM->execute_webhook_sync(itr->second, dpp::message(channel, embed));
                }
            }
            else
            {
                throw std::invalid_argument("channel " + channel + " not found");
            }
        }

        void Messenger::sendImage(const std::string &channel, const std::string &title,
                                  const std::string &message, const std::string &imagePath) const
        {
            auto itr = channelWebhookM.find(channel);
            if (itr != channelWebhookM.end())
            {
                sendEmbed(channel, title, message);

                dpp::message msg(channel, "");
                msg.add_file(title, dpp::utility::read_file(imagePath));
                dpp::embed embed = dpp::embed()
                                       .set_color(dpp::colors::sti_blue)
                                       .set_timestamp(time(0));
                embed.set_image("attachment://" + title); // reference to the attached file
                msg.add_embed(embed);
                botM->execute_webhook_sync(itr->second, dpp::message(channel, embed));
            }
            else
            {
                throw std::invalid_argument("channel " + channel + " not found");
            }
        }

        void Messenger::sendMessage(const std::string &channel, const std::string &message) const
        {
            auto itr = channelWebhookM.find(channel);
            if (itr != channelWebhookM.end())
            {
                std::vector<std::string> chunks = Utility::divideInChunks(message);
                for (auto &chunk : chunks)
                {
                    botM->execute_webhook_sync(itr->second, dpp::message(message));
                }
            }
            else
            {
                throw std::invalid_argument("channel " + channel + " not found");
            }
        }

        void Messenger::addWebhook(const std::string &channel, const std::string &webhook)
        {
            if (channelWebhookM.find(channel) == channelWebhookM.end())
            {
                channelWebhookM.insert({channel, webhook});
            }
            else
            {
                throw std::invalid_argument("channel " + channel + " already exists");
            }
        }

        const std::map<std::string, std::string> &Messenger::getChannelWebhooks() const
        {
            return channelWebhookM;
        }
    }
}
