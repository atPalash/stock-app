#include <iostream>

#include "listener.h"
#include "messenger.h"
#include "server.h"

void initListener(std::string token)
{
    DiscordConnector::Listener discordListener{token};
}

int main()
{
    std::cout << "Hello Discord!";

    /* Setup the bot */
    std::string token = "OTA2MzIyOTY2MTAxNDk1ODM4.YYW9CQ.ubld8BfYpa7s60hU2yU48Pr7gA4";

    // Start thread t1
    std::thread listenerThread(initListener, token);

    /* construct a webhook object using the URL you got from Discord */
    std::string wh{"https://discord.com/api/webhooks/961329477785387008/yAYntyDBdRLX56vi78BlSNAgf64ZQ_Ae5ekJzOc0f93XAGV5pQ0U016VBrV3gaLF5FPm"};

    DiscordConnector::Messenger discordMessenger{token};
    discordMessenger.addWebhook("general", wh);
    discordMessenger.sendEmbed("general", "Discord bot online", "Now you can interact with discord");

    DiscordConnector::Server server{8081, token};
    server.run();

    listenerThread.join();
    return 0;
}