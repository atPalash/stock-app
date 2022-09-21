#pragma once

#include <iostream>
#include <memory>

#include <dpp/dpp.h>

namespace DiscordConnector
{
    /**
     * @brief A class to communicate with Discord. Listen to command coming from
     * different channels. Ideally user should interact through query channel only.
     *
     * @param bot token.
     */
    class Listener
    {
    public:
        Listener(std::string &token);
        ~Listener();

    private:
        /**
         * @brief Startup the discord listener service.
         *
         */
        void init();

    private:
        std::string &tokenM;
        std::unique_ptr<dpp::cluster> botM;
    };
}
