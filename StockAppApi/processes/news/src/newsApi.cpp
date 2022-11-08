#include "newsApi.h"

#include <chrono>
#include "date/date.h"

#include "boost/format.hpp"
#include "nlohmann/json.hpp"
#include "cpr/cpr.h"

namespace
{
    cpr::Response httpGet(std::string query, std::string from, std::string sortBy, std::string searchIn, std::string language = "en")
    {
        try
        {
            std::string queryUrl = (boost::format("%sq=%s&from=%s&sortBy=%s&searchIn=%s&language=%s&apiKey=%s") % News::Src::url % query % from % sortBy % searchIn % language % News::Src::API_KEY).str();
            cpr::Response r = cpr::Get(cpr::Url{queryUrl});
            return r;
        }
        catch (const std::exception &e)
        {
            throw;
            // return cpr::Response();
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

namespace News
{
    namespace Src
    {
        //     std::string getNewsInDiscordFormat(std::string query,
        //                                        std::string from,
        //                                        std::string sortBy,
        //                                        std::string searchIn,
        //                                        std::string language,
        //                                        int count)
        //     {
        //         try
        //         {
        //             if (from == "")
        //             {
        //                 auto todaysDate = date::floor<date::days>(std::chrono::system_clock::now());
        //                 date::year_month_day prev1Month = todaysDate - date::days{30};
        //                 if (prev1Month.ok())
        //                 {
        //                     from = (boost::format("%1%-%2%-%3%") % prev1Month.year() % prev1Month.month() % prev1Month.day()).str();
        //                 }
        //                 else
        //                 {
        //                     throw std::runtime_error("from date not formated properly");
        //                 }
        //             }

        //             cpr::Response res = httpGet(query, from, sortBy, searchIn);

        //             if (!res.error)
        //             {
        //                 auto articles = getArticlesN(res.text, 10);
        //                 return articles;
        //             }
        //             else
        //             {
        //                 throw std::runtime_error("Error occured while fetching articles");
        //             }
        //         }
        //         catch (const std::exception &e)
        //         {
        //             throw;
        //             // return e.what();
        //         }
        //     }
    }
}