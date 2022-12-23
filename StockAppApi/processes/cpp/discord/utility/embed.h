#pragma once

#include <vector>
#include <string>

namespace DiscordConnector
{
    namespace Utility
    {
#define EMBED_CHUNK_SIZE = 4096;
        /**
         * @brief send message to discord in chunks. We send chunks of @ref EMBED_CHUNK_SIZE
         *
         * @param message to divide
         * @return std::vector<std::string> chunks of messages
         */
        std::vector<std::string> divideInChunks(std::string message);
    }
}