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
            inline static void LogInfo(const std::string &file, int line, const std::string &message) { LogToFile(Info, file, line, message); };
            inline static void LogError(const std::string &file, int line, const std::string &message) { LogToFile(Error, file, line, message); };
            inline static void LogCritical(const std::string &file, int line, const std::string &message)  { LogToFile(Critical, file, line, message); };
            static void LogToFile(LogLevel level, const std::string &file, int line, const std::string &message);
        
        private:
            static std::shared_ptr<spdlog::logger> sFileLogger;
        };
    }
}