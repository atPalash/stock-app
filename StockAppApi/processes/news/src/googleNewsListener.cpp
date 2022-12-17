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
        GoogleNewsListener::GoogleNewsListener(const std::string &stockListYaml,
                                               int interval, const std::string &masterUrl) : configM(stockListYaml),
                                                                                             intervalM(interval), stopM(false),
                                                                                             masterUrlM(masterUrl)
        {
        }

        void GoogleNewsListener::run()
        {
            while (!stopM)
            {
                try
                {
                    readConfig();
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
                                    else
                                    {
                                        latestNewsM[stock].isSentToDiscord = true;
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
            std::string toSendTemplate = "sendEmbed --channel general --message ";
            std::string toSend = toSendTemplate;
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

            if (toSend != toSendTemplate)
            {
                Base::Src::post(masterUrlM, toSend);
            }
        }

        void GoogleNewsListener::readConfig()
        {
            YAML::Node res = Base::Src::parseYaml(configM);

            for (auto i : res["stock"])
            {
                stockListM.push_back(i.as<std::string>());
            }

            for (auto i : res["topic"])
            {
                stockListM.push_back(i.as<std::string>());
            }
        }
    }
}