#include "logger.h"

#include <iomanip>
#include <iostream>

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

        void Log::LogToFile(LogLevel level, const std::string &file, int line, const std::string &message)
        {
            try
            {
                std::string logToFile = "[" + file + ":" + std::to_string(line) + "] " + message;
                switch (level)
                {
                case Info:
                    GetFileLogger()->info(logToFile);
                    break;
                case Error:
                    GetFileLogger()->error(logToFile);
                    break;
                case Critical:
                    GetFileLogger()->critical(logToFile);
                    break;
                default:
                    break;
                }
                GetFileLogger()->flush();
            }
            catch (std::exception &e)
            {
                std::cerr << e.what() << std::endl;
            }
        }
    }
}