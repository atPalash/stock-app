#include "googleNewsListener.h"

#include <unistd.h>
#include <iostream>

#include "boost/format.hpp"

#include "googleNewsRss.h"
#include "yamlParser.h"
#include "httpRequester.h"
#include "logger.h"

namespace News
{
    namespace Src
    {
        GoogleNewsListener::GoogleNewsListener(std::string stockListYaml,
                                               int interval, std::string masterUrl) : intervalM(interval), stopM(false),
                                                                                      masterUrlM(masterUrl)
        {
            YAML::Node res = Base::Src::parseYaml(stockListYaml);

            for (auto i : res["latest"])
            {
                stockListM.push_back(i.as<std::string>());
            }
        }

        void GoogleNewsListener::run()
        {
            while (!stopM)
            {
                try
                {
                    for (auto stock : stockListM)
                    {
                        try
                        {
                            auto articles = getNews(stock, 1);
                            if (articles.size() > 0)
                            {
                                if (latestNewsM.find(stock) != latestNewsM.end())
                                {
                                    if (latestNewsM[stock].info.headline != articles[0].headline)
                                    {
                                        latestNewsM[stock].isSentToDiscord = false;
                                        latestNewsM[stock].info = articles[0];
                                    }
                                }
                                else
                                {
                                    latestNewsM.insert({stock, LatestNews{false, articles[0]}});
                                }
                            }
                        }
                        catch (std::exception &e)
                        {
                            Base::Src::Log::LogCritical(__FILE__, __LINE__, e.what());
                        }
                    }
                }
                catch (std::exception &e)
                {
                    throw;
                }
                sendDiscordMessage();
                sleep(intervalM * 60);
            }
        }

        void GoogleNewsListener::stop()
        {
            stopM = true;
        }

        void GoogleNewsListener::sendDiscordMessage()
        {
            std::string toSend = "sendEmbed --channel general --message ";
            for (auto news : latestNewsM)
            {
                if (!news.second.isSentToDiscord)
                {
                    toSend += (boost::format("[%1%. %2%](%3%)\n") %
                               news.first % news.second.info.headline %
                               news.second.info.link)
                                  .str();
                }
            }

            if (toSend != "")
            {
                Base::Src::post(masterUrlM, toSend);
            }
        }
    }
}