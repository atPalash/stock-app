#include "messageParser.h"

#include <boost/algorithm/string.hpp>

namespace DiscordConnector
{
    std::map<std::string, std::string> parseMessage(std::string message)
    {
        try
        {
            std::string messageToParse{message};
            boost::trim(messageToParse);
            std::vector<std::string> messageArr;
            boost::split(messageArr, messageToParse, boost::is_any_of(" "));
            printf("{%s}", messageToParse.c_str());

            std::map<std::string, std::string> result;

            // first element is always command
            result.insert({"command", messageArr[0]});
            for (auto it = messageArr.begin() + 1; it != messageArr.end(); ++it)
            {
                if (it->find("??") != std::string::npos)
                {
                    it->erase(0, 2);
                    result.insert({*it, *++it});
                }
            }

            return result;
        }
        catch (const std::exception &e)
        {
            printf("{%s}", e.what());
            throw;
        }
    }
}
