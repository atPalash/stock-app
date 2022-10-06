#include "embed.h"

#include <boost/algorithm/string.hpp>

namespace DiscordConnector
{
    namespace Utility
    {
        std::vector<std::string> divideInChunks(std::string message)
        {
            std::vector<std::string> chunks;

            boost::trim(message);
            std::vector<std::string> messageArr;
            boost::split(messageArr, message, boost::is_any_of("\n"));

            std::string chunk;
            for (auto &msg : messageArr)
            {
                if ((chunk + msg).size() < 4096)
                {
                    chunk += msg;
                }
                else
                {
                    chunks.push_back(chunk);
                    chunk.clear();
                }
            }

            if (chunk.size() > 0)
            {
                chunks.push_back(chunk);
            }

            return chunks;
        }
    }
}