#include "logger.h"

#include <iomanip>

#include "spdlog/sinks/stdout_color_sinks.h"
#include "spdlog/sinks/basic_file_sink.h"
#include "spdlog/async.h"

namespace Base
{
    namespace Src
    {
        std::shared_ptr<spdlog::logger> Log::sCoreLogger;
        std::shared_ptr<spdlog::logger> Log::sClientLogger;
        std::shared_ptr<spdlog::logger> Log::sFileLogger;

        void Log::Init()
        {
            // spdlog::set_pattern("%^[%T] %n: %v%s");

            sCoreLogger = spdlog::stdout_color_mt("StockAppApi");
            sCoreLogger->set_level(spdlog::level::trace);

            sClientLogger = spdlog::stdout_color_mt("StockAppApi_client");
            sClientLogger->set_level(spdlog::level::trace);

            auto t = std::time(nullptr);
            auto tm = *std::localtime(&t);

            std::ostringstream oss;
            oss << "/home/palash/dev/stock-app/StockAppApi/logs/" << std::put_time(&tm, "%Y-%m-%d %H-%M-%S") << ".log";
            sFileLogger = spdlog::basic_logger_mt<spdlog::async_factory>("StockLogger", oss.str());
            sFileLogger->set_level(spdlog::level::trace);
        }
    }
}