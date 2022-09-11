#include "server.h"

// install crow to usr/local
#include "crow.h" 

void handle_get()
{
    crow::SimpleApp app;

    CROW_ROUTE(app, "/")([](){
        return "Hello world";
    });

    app.port(18080).run();
}