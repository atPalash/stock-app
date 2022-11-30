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
            for (int i = 0; i < messageArr.size(); i++)
            {
                if ((chunk + messageArr[i]).size() < 4096)
                {
                    chunk += messageArr[i] + "\n";
                }
                else
                {
                    chunks.push_back(chunk);
                    chunk.clear();
                    i--; // get the last message again
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