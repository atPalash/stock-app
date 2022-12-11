#pragma once

#include <string>
#include <vector>

namespace News
{
    namespace Src
    {
        /**
         * @brief A data type to store headline and link to the news.
         *
         */
        struct Info
        {
            std::string headline;
            std::string link;
        };

        /**
         * @brief https://news.google.com/rss is the source of news
         */
        const std::string BASE_URL = "https://news.google.com/rss/search?";

        /**
         * @brief Get a list of news related to the query. Each item is of the
         * format { "headline": "title of headline",
         *          "link": "link of news" }
         *
         * @param query string to search
         * @param count max number of articles needed
         * @param searchIn title, description, content. e.g. intitle, indescription.
         * Space between search parameters are replaced by %20.
         * @param when can be 1h, 1y etc. Currently not used.
         * @param language of article
         * @param country of news
         * @return list of dictionary
         */
        std::vector<Info> getNews(std::string query,
                                  int count = 10,
                                  std::string searchIn = "",
                                  std::string when = "1d",
                                  std::string language = "en",
                                  std::string country = "IN");

        /**
         * @brief Get the News In Discord formatted string, such that the string
         * is a clickable type to the entire news in discord.
         *
         * @param query string to search
         * @param count max number of articles needed
         * @param searchIn title, description, content. e.g. intitle, indescription.
         * Space between search parameters are replaced by %20.
         * @param when can be 1h, 1y etc. Currently not used.
         * @param language of article
         * @param country of news
         * @return std::string
         */
        std::string getNewsInDiscordFormat(std::string query,
                                           int count = 10,
                                           std::string searchIn = "",
                                           std::string when = "1d",
                                           std::string language = "en",
                                           std::string country = "IN");
    }
}