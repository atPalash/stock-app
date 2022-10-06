#include "newsApi.h"

#include <chrono>

#include "boost/format.hpp"
#include "nlohmann/json.hpp"

namespace News
{
    namespace Src
    {
        std::string getNews(std::string query, std::string from = "",
                            std::string sortBy = "", std::string searchIn = "",
                            std::string language = "")
        {
            try
            {
                if (from == "")
                {
                    auto now = std::chrono::system_clock::now();
                    from = "2022-10-02";
                }

                if (sortBy == "")
                {
                    sortBy = "publishedAt";
                }
                cpr::Response res = httpGet(query, from, sortBy, "title,description");

                if (!res.error)
                {
                    auto articles = getArticlesN(res.text, 10);
                    return articles;
                }
                else
                {
                    return res.error.message;
                }
            }
            catch (const std::exception &e)
            {
                return e.what();
            }
        }

        cpr::Response httpGet(std::string query, std::string from, std::string sortBy, std::string searchIn)
        {
            try
            {
                std::string queryUrl = (boost::format("%sq=%s&from=%s&sortBy=%s&searchIn=%s&apiKey=%s") % url % query % from % sortBy % searchIn % API_KEY).str();
                cpr::Response r = cpr::Get(cpr::Url{queryUrl});
                return r;
            }
            catch (const std::exception &e)
            {
                return cpr::Response();
            }
        }

        std::vector<std::string> getArticles(std::string data)
        {
            try
            {
                nlohmann::json newsJson = nlohmann::json::parse(data);
                std::vector<std::string> articles;

                int newsCount = 0;
                for (auto &article : newsJson["articles"])
                {
                    newsCount++;
                    std::string news = (boost::format("[%1%.%2%](%3%)\n") % newsCount % article["title"] % article["url"]).str();
                    articles.push_back(news);
                }

                return articles;
            }
            catch (const std::exception &e)
            {
                throw;
            }
        }

        std::string getArticlesN(std::string data, int numberOfArticles)
        {
            std::vector<std::string> articles = getArticles(data);
            std::string ret;

            for (int i = 0; i < numberOfArticles; i++)
            {
                ret += articles[i];
            }

            return ret;
        }
    }
}