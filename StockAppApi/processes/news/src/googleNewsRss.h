#pragma once

#include <string>
#include <vector>
#include <map>

namespace News
{
    namespace Src
    {
        struct info
        {
            std::string headline;
            std::string link;
        };

        /**
         * @brief https://newsapi.org/ is the source of news, the constants e.g.
         * API key and url are defined here. TODO
         */
        const std::string BASE_URL = "https://news.google.com/rss/search?";

        /**
         * @brief Get a list of news related to the query. Each item is of the
         * format { "headline": "title of headline",
         *          "link": "link of news" }
         *
         * @param query string to search
         * @param searchIn title, description, content. e.g. title,description.
         * No space between search parameters.
         * @param when date in YYYY-MM-DD format
         * @param language of article
         * @param country of news
         * @param count max number of articles needed
         * @return list of dictionary
         */
        std::vector<info> getNews(std::string query,
                                  std::string searchIn = "intitle",
                                  std::string when = "1y",
                                  std::string language = "en",
                                  std::string country = "IN",
                                  int count = 10);

        std::string getNewsInDiscordFormat(std::string query,
                                           std::string searchIn = "intitle",
                                           std::string when = "30d",
                                           std::string language = "en",
                                           std::string country = "IN",
                                           int count = 10);
    }
}