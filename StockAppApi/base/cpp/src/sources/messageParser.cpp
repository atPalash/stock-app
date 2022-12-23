#include "messageParser.h"

#include <string>

#include <boost/algorithm/string.hpp>

namespace Base
{
    namespace Src
    {
        std::vector<std::string> splitString(const std::string &delimiter, const std::string &textToSplit)
        {
            size_t pos = 0;
            std::vector<std::string> tokens;
            std::string tempText = textToSplit;
            while ((pos = tempText.find(delimiter)) != std::string::npos) {
                tokens.push_back(tempText.substr(0, pos));
                tempText.erase(0, pos + delimiter.length());
            }

            tokens.push_back(tempText);
            return tokens;
        }

        std::map<std::string, std::string> parseMessage(const std::string &message, const std::string &parserSymbol)
        {
            try
            {
                std::string messageToParse{message};
                boost::trim(messageToParse);
                std::vector<std::string> messageArr = splitString(parserSymbol, message);
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
