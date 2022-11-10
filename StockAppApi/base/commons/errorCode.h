#pragma once

namespace Base
{
    namespace Commons
    {
        /**
         * @brief Error code similar to http error codes. Not using all.
         *
         */
        enum HttpErrorCode
        {
            None = 200,
            BadRequest = 400,
            MethodNotAllowed = 405
        };
    }
}