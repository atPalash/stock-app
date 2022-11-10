#pragma once

#include "spdlog/spdlog.h"

namespace Base
{
    namespace Src
    {
        class Log
        {
        public:
            static void Init();
            inline static std::shared_ptr<spdlog::logger> &GetCoreLogger() { return sCoreLogger; }
            inline static std::shared_ptr<spdlog::logger> &GetClientLogger() { return sClientLogger; }
            inline static std::shared_ptr<spdlog::logger> &GetFileLogger() { return sFileLogger; }

        private:
            static std::shared_ptr<spdlog::logger> sCoreLogger;
            static std::shared_ptr<spdlog::logger> sClientLogger;
            static std::shared_ptr<spdlog::logger> sFileLogger;
        };
    }
}

// // core log macros
// #define SA_CORE_TRACE(...) Base::Src::Log::GetCoreLogger()->trace(__VA_ARGS__)
// #define SA_CORE_INFO(...) StockAppApi::logger::Log::GetCoreLogger()->info(__VA_ARGS__)
// #define SA_CORE_WARN(...) StockAppApi::logger::Log::GetCoreLogger()->warn(__VA_ARGS__)
// #define SA_CORE_ERROR(...) StockAppApi::logger::Log::GetCoreLogger()->error(__VA_ARGS__)
// #define SA_CORE_FATAL(...) StockAppApi::logger::Log::GetCoreLogger()->fatal(__VA_ARGS__)

// // client log macros
// #define SA_CLIENT_TRACE(...) StockAppApi::logger::Log::GetClientLogger()->trace(__VA_ARGS__)
// #define SA_CLIENT_INFO(...) StockAppApi::logger::Log::GetClientLogger()->info(__VA_ARGS__)
// #define SA_CLIENT_WARN(...) StockAppApi::logger::Log::GetClientLogger()->warn(__VA_ARGS__)
// #define SA_CLIENT_ERROR(...) StockAppApi::logger::Log::GetClientLogger()->error(__VA_ARGS__)
// #define SA_CLIENT_FATAL(...) StockAppApi::logger::Log::GetClientLogger()->fatal(__VA_ARGS__)

// // Client log macros
// #define SA_TRACE(...) StockAppApi::logger::Log::GetClientLogger()->trace(__VA_ARGS__)
// #define SA_INFO(...) StockAppApi::logger::Log::GetClientLogger()->info(__VA_ARGS__)
// #define SA_WARN(...) StockAppApi::logger::Log::GetClientLogger()->warn(__VA_ARGS__)
// #define SA_ERROR(...) StockAppApi::logger::Log::GetClientLogger()->error(__VA_ARGS__)
// #define SA_CRITICAL(...) StockAppApi::logger::Log::GetClientLogger()->critical(__VA_ARGS__)

// File log macros
#define SA_FILE_TRACE(...) Base::Src::Log::GetFileLogger()->trace(__VA_ARGS__)
#define SA_FILE_INFO(...) Base::Src::Log::GetFileLogger()->info(__VA_ARGS__)
#define SA_FILE_WARN(...) Base::Src::Log::GetFileLogger()->warn(__VA_ARGS__)
#define SA_FILE_ERROR(...) Base::Src::Log::GetFileLogger()->error(__VA_ARGS__)
#define SA_FILE_CRITICAL(...) Base::Src::Log::GetFileLogger()->critical(__VA_ARGS__)
#define SA_FILE_FLUSH() Base::Src::Log::GetFileLogger()->flush()