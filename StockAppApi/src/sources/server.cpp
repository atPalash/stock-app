#include "server.h"

#include "logger.h"

namespace StockAppApi
{
    namespace server
    {
        Server::Server(int port) : portM(port) 
        {}

        Server::~Server() 
        {}
        
        void Server::run() {
            crow::SimpleApp app;

            CROW_ROUTE(app, "/")
            .methods("POST"_method)([](const crow::request& req){
                auto x = crow::json::load(req.body);
                if (!x)
                    return crow::response(400);

                std::ostringstream os;
                
                for(const auto key: x.keys())
                {
                    os << key << ": "<< x[key] << "\n";
                }

                SA_CORE_INFO(os.str());
                SA_FILE_INFO(os.str());
                return crow::response{os.str()};
            });

            app.port(portM).multithreaded().run();
        }
    }
}
