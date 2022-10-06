#include "commandHandler.h"

#include "boost/format.hpp"
#include "utility/messageParser.h"

namespace DiscordConnector
{
    namespace Src
    {
        Response CommandHandler::execute(std::string message)
        {
            std::map<std::string, std::string> parsedMessage = DiscordConnector::Utility::parseMessage(message, "--");
            std::string command = parsedMessage["command"];

            if (command == "headlines")
            {
                int index = 0;
                std::string title = "dummy";
                std::string link = "https://www.boost.org/doc/libs/1_49_0/libs/format/doc/format.html";
                std::string res = (boost::format("[%d. %s](%s)\n") % index % title % link).str();

                Response response{res, ErrorCode::None, std::exception()};
                return response;
            }
            else
            {
            }
        }
    }
}
