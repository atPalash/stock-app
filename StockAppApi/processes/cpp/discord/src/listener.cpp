#include "listener.h"

#include <cpr/cpr.h>

#include "messageParser.h"
#include "httpRequester.h"
#include "utility/embed.h"

namespace DiscordConnector
{
    namespace Src
    {
        Listener::Listener(const std::string &token,
                           const std::string &route) : tokenM(token),
                                                       routeM(route),
                                                       botM(new dpp::cluster(tokenM, dpp::i_default_intents | dpp::i_message_content))
        {
            init();
        };

        Listener::~Listener()
        {
            botM->shutdown();
        };

        void Listener::init()
        {
            auto embedFunc = [this](const dpp::message_create_t &event)
            {
                if (event.msg.author.username == "palash") /*(event.msg.author.username != this->botM->me.username)*/
                {
                    auto response = Base::Src::post(routeM, event.msg.content);

                    std::vector<std::string> chunks = Utility::divideInChunks(response.text);

                    for (auto &chunk : chunks)
                    {
                        /* create the embed */
                        dpp::embed embed = dpp::embed()
                                               .set_color(dpp::colors::sti_blue)
                                               .set_description(chunk)
                                               .set_timestamp(time(0));
                        /* reply with the created embed */
                        this->botM->message_create(dpp::message(event.msg.channel_id, embed).set_reference(event.msg.id));
                    }
                }
            };

            botM->on_message_create(embedFunc);
            botM->start(dpp::st_wait);
        }
    }
}
