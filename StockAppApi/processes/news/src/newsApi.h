#pragma once

#include <string>

#include <cpr/cpr.h>

namespace News
{
    namespace Src
    {
        /**
         * @brief https://newsapi.org/ is the source of news, the constants e.g.
         * API key and url are defined here.
         */
        const std::string API_KEY = "df5b7440992e47feb319e3fe7b209181";
        const std::string url = "https://newsapi.org/v2/everything?";

        /**
         * @brief Get the News In Discord Format string i.e [<index> title](link)
         * News in this format can be directly send to discord and viewed as an
         * embed message at Discord side.
         *
         * @param query string to search
         * @param from date in YYYY-MM-DD format
         * @param sortBy options are relevancy, popularity, publishedAt
         * @param searchIn title, description, content. e.g. title,description.
         * No space between search parameters.
         * @param language of article
         * @return std::string in discord link format
         */
        std::string getNewsInDiscordFormat(std::string query, std::string from = "",
                                           std::string sortBy = "", std::string searchIn = "",
                                           std::string language = "");
        cpr::Response httpGet(std::string query, std::string from,
                              std::string sortBy, std::string searchIn,
                              std::string language);
        std::vector<std::string> getArticles(std::string data);
        std::string getArticlesN(std::string data, int numberOfArticles);
    }
}