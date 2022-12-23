#include "httpRequester.h"

#include <iostream>

namespace Base
{
    namespace Src
    {
        void get(std::string url)
        {
        }

        cpr::Response post(std::string url, std::string message)
        {
            cpr::Response r = cpr::Post(cpr::Url{url},
                                        cpr::Body{message},
                                        cpr::Header{{"Content-Type", "text/plain"}});

            return r;
        }

        // void post(std::string url, std::map<std::string, std::string> message)
        // {
        //     // Not implemented
        //     // cpr::Response r = cpr::Post(cpr::Url{url},
        //     //                             cpr::Body{message},
        //     //                             cpr::Header{{"Content-Type", "text/json"}});
        //     // std::cout << r.text << std::endl;
        // }
    }
}
