#include "messageParser.h"

#include <iostream>

#include <boost/algorithm/string.hpp>

namespace DiscordConnector
{
    namespace Utility
    {
        std::map<std::string, std::string> parseMessage(const std::string &message, const std::string &parserSymbol)
        {
            try
            {
                std::string messageToParse{message};
                boost::trim(messageToParse);
                std::vector<std::string> messageArr;
                boost::split(messageArr, messageToParse, boost::is_any_of(" "));

                std::map<std::string, std::string> result;

                // first element is always command
                result.insert({"command", messageArr[0]});
                for (auto it = messageArr.begin() + 1; it != messageArr.end(); ++it)
                {
                    if (it->find(parserSymbol) != std::string::npos)
                    {
                        it->erase(0, 2);
                        result.insert({*it, *++it});
                    }
                }

                return result;
            }
            catch (const std::exception &e)
            {
                std::cerr << e.what() << std::endl;
                throw;
            }
        }
    }
}
