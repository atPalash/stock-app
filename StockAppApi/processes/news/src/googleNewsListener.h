#pragma once

#include <string>
#include <map>
#include <vector>

#include "googleNewsRss.h"

namespace News
{
    namespace Src
    {
        struct LatestNews
        {
            bool isSentToDiscord;
            News::Src::Info info;
        };

        class GoogleNewsListener
        {
        public:
            /**
             * @brief news listener with stocklist to listen on topic and the
             * interval
             *
             * @param stockListYaml list of selected stocks in yaml
             * @param interval polling interval in minutes
             */
            GoogleNewsListener(std::string stockListYaml, int interval, std::string masterUrl);
            ~GoogleNewsListener(){};

            /**
             * @brief start polling google rss for new news.
             */
            void run();

            void stop();

        private:
            /**
             * @brief send the list of latest news to discord
            */
            void sendDiscordMessage();

        private:
            int intervalM;
            std::vector<std::string> stockListM;
            std::map<std::string, LatestNews> latestNewsM;
            std::string masterUrlM;
            bool stopM;
        };
    }
}