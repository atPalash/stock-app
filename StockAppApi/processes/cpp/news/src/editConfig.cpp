#include "editConfig.h"

namespace News
{
    namespace Src
    {
        bool edit(const std::string &key,
                                      const std::string &value,
                                      Base::Src::Operation operation,
                                      const std::string& filePath)
        {
            try
            {
                Base::Src::editYaml(key, value, operation, filePath);
                return true;
            }
            catch(const std::exception& e)
            {
                throw;
            }
        }
    }
}