#pragma once

#include <iostream>
#include <memory>

#include <dpp/dpp.h>

namespace DiscordConnector
{
    namespace Src
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
            Listener(const std::string &token, const std::string &route);
            ~Listener();

        private:
            /**
             * @brief Startup the discord listener service.
             *
             */
            void init();

            /**
             * @brief post listener error to the parent server address, such that it can be
             * notified to user
             *
             * @param errorMessage defining what caused the error
             */
            void postListenerError(const std::string &errorMessage);

        private:
            const std::string &tokenM;
            const std::string &routeM;
            std::unique_ptr<dpp::cluster> botM;
        };

    } // namespace Src
} // namespace DiscordConnector
