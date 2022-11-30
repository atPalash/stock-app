#include "googleNewsRss.h"

#include "boost/format.hpp"
#include <boost/algorithm/string/replace.hpp>

#include "cpr/cpr.h"
#include "pugixml.hpp"

namespace
{
    cpr::Response httpGet(std::string queryUrl)
    {
        try
        {
            cpr::Response r = cpr::Get(cpr::Url{queryUrl});
            return r;
        }
        catch (const std::exception &e)
        {
            throw;
        }
    }

    std::vector<News::Src::info> getArticles(std::string data,
                                             int count = 10)
    {
        std::vector<News::Src::info> articles;
        try
        {
            pugi::xml_document doc;
            pugi::xml_parse_result result = doc.load_string(data.c_str());
            if (!result)
                throw std::runtime_error("Couldnot load xml");

            int articleCount = 1;
            for (auto item : doc.child("rss").child("channel").children("item"))
            {
                std::string title(item.child("title").first_child().value());
                std::string link(item.child("link").first_child().value());

                News::Src::info newsLink{title, link};
                articles.push_back(newsLink);
                articleCount++;

                if (articleCount > count)
                {
                    break;
                }
            }

            return articles;
        }
        catch (const std::exception &e)
        {
            throw;
        }
    }
}

namespace News
{
    namespace Src
    {
        std::vector<info> getNews(std::string query,
                                  std::string searchIn,
                                  std::string when,
                                  std::string language,
                                  std::string country,
                                  int count)
        {
            try
            {
                std::string queryUrl = News::Src::BASE_URL + "q=" + searchIn +
                                       ":" + query + "&hl=" + language + "-" +
                                       country + "&gl=" + country + "&ceid=" +
                                       country + ":" + language;
                cpr::Response res = httpGet(queryUrl);

                if (!res.error)
                {
                    auto articles = getArticles(res.text, count);
                    return articles;
                }
                else
                {
                    throw std::runtime_error("Error occured while fetching articles");
                }
            }
            catch (const std::exception &e)
            {
                throw;
            }
        }

        std::string getNewsInDiscordFormat(std::string query,
                                           std::string searchIn,
                                           std::string when,
                                           std::string language,
                                           std::string country,
                                           int count)
        {
            try
            {
                boost::replace_all(query, " ", "%20");
                auto articles = getNews(query, searchIn, when, language, country,
                                        count);

                std::string ret;
                int newsCount = 1;
                for (auto &article : articles)
                {
                    std::string news = (boost::format("[%1%. %2%](%3%)\n") % newsCount % article.headline % article.link).str();
                    ret += news;
                    newsCount++;
                }

                return ret;
            }
            catch (const std::exception &e)
            {
                throw;
            }
        }
    }
}