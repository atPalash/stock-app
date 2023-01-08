#pragma once

#include <dpp/dpp.h>

namespace DiscordConnector
{
    namespace Src
    {
        /**
         * @brief Discord messenger to send message to channel. The user adds the
         * channel name and the webhooks after creating the object.
         */
        class Messenger
        {
        public:
            Messenger(const std::string &token);
            Messenger();
            ~Messenger();

            /**
             * @brief Send an embedded message to a Discord channel.
             *
             * @param channel name
             * @param title of message
             * @param message to send
             */
            void sendEmbed(const std::string &channel, const std::string &title, const std::string &message) const;

            /**
             * @brief Send a message to a Discord channel.
             *
             * @param channel name
             * @param message to send
             */
            void sendImage(const std::string &channel, const std::string &title,
                           const std::string &message, const std::string &imagePath) const;

            /**
             * @brief Send a message to a Discord channel.
             *
             * @param channel name
             * @param message to send
             */
            void sendMessage(const std::string &channel, const std::string &message) const;

            /**
             * @brief add channel name and webhook for webhook based discord message
             *
             * @param channel name
             * @param webhook URL you got from Discord
             */
            void addWebhook(const std::string &channel, const std::string &webhook);

            /**
             * @brief Get the registered Channel with its Webhook
             *
             * @return const std::map<std::string, std::string>& channelName : webhook
             */
            const std::map<std::string, std::string> &getChannelWebhooks() const;

        private:
            const std::string &tokenM;
            std::unique_ptr<dpp::cluster> botM;
            std::map<std::string, std::string> channelWebhookM;
        };
    }
}