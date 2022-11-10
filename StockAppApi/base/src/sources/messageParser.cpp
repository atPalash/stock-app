#include "messageParser.h"

#include <string>

#include <boost/algorithm/string.hpp>

namespace Base
{
    namespace Src
    {
        std::map<std::string, std::string> parseMessage(const std::string &message, const std::string &parserSymbol)
        {
            try
            {
                std::string messageToParse{message};
                boost::trim(messageToParse);
                std::vector<std::string> messageArr;
                boost::split(messageArr, messageToParse, boost::is_any_of(parserSymbol));
                std::map<std::string, std::string> result;

                // first element is always command
                boost::trim(messageArr[0]); // trim spaces
                result.insert({"command", messageArr[0]});
                for (auto it = messageArr.begin() + 1; it != messageArr.end(); ++it)
                {
                    if (*it != "")
                    {
                        // get the first space position
                        auto spacePos = it->find(" ");

                        // element on left of first space is the argument
                        std::string arg = it->substr(0, spacePos);
                        boost::trim(arg);
                        // rest is the arg value.
                        std::string value = it->substr(spacePos + 1, it->length());
                        boost::trim(value);
                        result.insert({arg, value});
                    }
                }

                return result;
            }
            catch (const std::exception &e)
            {
                throw;
            }
        }
    }
}
