#pragma once

#include "spdlog/spdlog.h"

namespace Base
{
    namespace Src
    {
        class Log
        {
        public:
            enum LogLevel
            {
                Info,
                Error,
                Critical
            };

        public:
            static void Init(std::string identifier);
            inline static std::shared_ptr<spdlog::logger> &GetFileLogger() { return sFileLogger; }
            static void LogInfo(const std::string &file, int line, const std::string &message)
            {
                std::string logToFile = "[" + file + "/" + std::to_string(line) + "] " + message;
                GetFileLogger()->info(logToFile);
                GetFileLogger()->flush();
            };

            static void LogError(const std::string &file, int line, const std::string &message)
            {
                std::string logToFile = "[" + file + "/" + std::to_string(line) + "] " + message;
                GetFileLogger()->error(message);
                GetFileLogger()->flush();
            };

            static void LogCritical(const std::string &file, int line, const std::string &message)
            {
                std::string logToFile = "[" + file + "/" + std::to_string(line) + "] " + message;
                GetFileLogger()->critical(message);
                GetFileLogger()->flush();
            };

        private:
            static std::shared_ptr<spdlog::logger> sFileLogger;
        };
    }
}

// File log macros
#define SA_FILE_TRACE(...) Base::Src::Log::GetFileLogger()->trace(__VA_ARGS__)
#define SA_FILE_INFO(...) Base::Src::Log::GetFileLogger()->info(__VA_ARGS__)
#define SA_FILE_WARN(...) Base::Src::Log::GetFileLogger()->warn(__VA_ARGS__)
#define SA_FILE_ERROR(...) Base::Src::Log::GetFileLogger()->error(__VA_ARGS__)
#define SA_FILE_CRITICAL(...) Base::Src::Log::GetFileLogger()->critical(__VA_ARGS__)
#define SA_FILE_FLUSH() Base::Src::Log::GetFileLogger()->flush()