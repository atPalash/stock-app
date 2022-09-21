#include "messenger.h"

namespace DiscordConnector
{
    Messenger::Messenger(std::string &token) : tokenM(token),
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
        dpp::embed embed = dpp::embed()
                               .set_color(dpp::colors::sti_blue)
                               .set_title(title)
                               .set_description(message)
                               .set_timestamp(time(0));

        auto itr = channelWebhookM.find(channel);
        if (itr != channelWebhookM.end())
        {
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
            botM->execute_webhook_sync(itr->second, dpp::message(message));
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

    const std::map<std::string, std::string> &Messenger::getChannelWebhook() const
    {
        return channelWebhookM;
    }
}
