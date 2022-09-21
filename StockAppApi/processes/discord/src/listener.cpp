#include "listener.h"

#include "messageParser.h"

namespace DiscordConnector
{
    Listener::Listener(std::string &token) : tokenM(token),
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
            auto parsedMessageMap = DiscordConnector::parseMessage(event.msg.content);
            if (event.msg.author.username != this->botM->me.username)
            {
                /* create the embed */
                dpp::embed embed = dpp::embed()
                                       .set_color(dpp::colors::sti_blue)
                                       .set_title(parsedMessageMap["command"])
                                       .set_description("Dummy description")
                                       .set_timestamp(time(0));
                /* reply with the created embed */
                this->botM->message_create(dpp::message(event.msg.channel_id, embed).set_reference(event.msg.id));
            }
        };

        botM->on_message_create(embedFunc);
        botM->start(dpp::st_wait);
    }
}
