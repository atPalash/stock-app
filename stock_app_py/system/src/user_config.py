import ast
import json
import pandas

from stock_app_py.system.base.system import System
from stock_app_py.system.interface.system_if import RetVal
from stock_app_py.utility.src.path_helper import get_app_path


class UserConfig(System):
    def __init__(
        self,
        indicator_config_file: str,
        selected_stocks_config_file: str,
        parameter: dict,
        command_handler: object,
        name="",
    ) -> None:
        """Save and read user config based on user. Currently identify user with
        ip username. This will be updated to username. Client can request config
        snapshot based on snapshot name or can fetch all snapshots at once. Client
        can request to add new snapshot or update existing one.

        e.g. userconfig --do get --indicator <snapshot name>/<all>,
        userconfig --do update --indicator <snapshot name>
        Args:
            indicator_config_file (str): indicator configuration
            selected_stocks_config_file (str): selected stocks list
            parameter (dict): key-value pairs for setting up the query
            command_handler (object): to call other systems
            name (str, optional): Name of the query. Defaults to "".
        """
        super().__init__(
            indicator_config_file=indicator_config_file,
            selected_stocks_config_file=selected_stocks_config_file,
            parameter=parameter,
            command_handler=command_handler,
            name=name,
        )

        self.commands = {
            "get": self.__get,
            "update": self.__update,
            "remove": self.__remove,
        }
        self.users_config = get_app_path("users_config.json")

    def __get(self) -> RetVal:
        """Return snapshot config or all snapshots.

        Returns:
            RetVal: selected stock config
        """
        ret = None
        err = ""
        try:
            req_data = ast.literal_eval(self.parameter["json"])
            username = req_data["username"]
            password = req_data["password"]
            with open(self.users_config, "r") as f:
                # Read file
                data = f.read()
                data = json.loads(data)
            if username in data and data[username]["password"] == password:
                ret = {
                    "ok": True,
                    "query": data[username]["query"],
                    "chart": data[username]["chart"],
                }
        except Exception as e:
            err = e.args[0]
        return RetVal(obj=ret, obj_as_str="dict of snapshots", errors=err)

    def __update(self) -> RetVal:
        """Update the config with name

        Returns:
            RetVal: None
        """
        err = ""
        try:
            # Open a file for writing
            with open(self.users_config, "r+") as f:
                saved_config = f.read()
                saved_config = json.loads(saved_config)
                req_data = ast.literal_eval(self.parameter["json"])
                username = req_data["username"]
                config_type = req_data["configType"]
                config_id = req_data["configId"]
                if config_type == "chart":
                    # TODO
                    queries = req_data["queries"]
                    saved_config[username][config_type]["configs"][config_id] = {
                        "queries": queries
                    }
                else:
                    queries = req_data["queries"]
                    # config["react"][self.parameter["indicator"]] = data
                    saved_config[username][config_type]["configs"][config_id] = {
                        "queries": queries
                    }
                f.seek(0)
                json.dump(saved_config, f, indent=4)
                f.truncate()
        except Exception as e:
            err = e.args[0]
        return RetVal(obj="", obj_as_str="None", errors=err)

    def __remove(self) -> RetVal:
        """Remove the config
        Returns:
            RetVal: None
        """
        err = ""
        try:
            # Open a file for writing
            with open(self.users_config, "r+") as f:
                saved_config = f.read()
                saved_config = json.loads(saved_config)
                req_data = ast.literal_eval(self.parameter["json"])
                username = req_data["username"]
                config_id = req_data["configId"]
                del saved_config[username]["configs"][config_id]
                f.seek(0)
                json.dump(saved_config, f, indent=4)
                f.truncate()
        except Exception as e:
            err = e.args[0]
        return RetVal(obj="", obj_as_str="None", errors=err)

    def debug_update(self):
        self.__update()


if __name__ == "__main__":
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    yf = UserConfig(
        indicator_config_file=indicator_config_yaml,
        selected_stocks_config_file=selected_stocks_yaml,
        parameter={},
        command_handler=None,
        name="",
    )
    # https://www.niftyindices.com/IndexConstituent/ind_niftyautolist.csv
    # https://www.niftyindices.com/IndexConstituent/nifty_low_Volatility50_Index.csv
    # https://www.niftyindices.com/IndexConstituent/ind_niftyoilgaslist.csv
    # javascript:;
    data = yf.debug_update()
    print(data)
