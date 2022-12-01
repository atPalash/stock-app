#include "logger.h"

#include <iomanip>

#include "spdlog/sinks/stdout_color_sinks.h"
#include "spdlog/sinks/basic_file_sink.h"
#include "spdlog/async.h"

namespace Base
{
    namespace Src
    {
        std::shared_ptr<spdlog::logger> Log::sFileLogger;

        void Log::Init(std::string identifier)
        {
            auto t = std::time(nullptr);
            auto tm = *std::localtime(&t);

            std::stringstream logStream;
            logStream << "/home/palash/dev/stock-app/StockAppApi/logs/"
                      << std::put_time(&tm, "%Y-%m-%d") << ".log";
            sFileLogger = spdlog::basic_logger_mt<spdlog::async_factory>(identifier, logStream.str());
            sFileLogger->set_level(spdlog::level::trace);
        }
    }
}