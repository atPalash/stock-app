import ast
import json

from stock_app_py.system.base.system import System
from stock_app_py.system.interface.system_if import RetVal
from stock_app_py.utility.src.path_helper import get_app_path


class UserLogin(System):
    def __init__(
        self,
        indicator_config_file: str,
        selected_stocks_config_file: str,
        parameter: dict,
        command_handler: object,
        name="",
    ) -> None:
        """TODO.

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
            # "update": self.__update, # Add user hardcoded
        }
        self.users_config = get_app_path("users_config.json")

    def __get(self) -> RetVal:
        """TODO
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
                ret = {"ok": True, "configs": data[username]["configs"]}
        except Exception as e:
            err = e.args[0]
        return RetVal(obj=ret, obj_as_str="dict of snapshots", errors=err)

    def debug_update(self):
        self.__get()


if __name__ == "__main__":
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    yf = UserLogin(
        indicator_config_file=indicator_config_yaml,
        selected_stocks_config_file=selected_stocks_yaml,
        parameter={"json": {"username": "palash", "password": "palash1988"}},
        command_handler=None,
        name="",
    )
    # https://www.niftyindices.com/IndexConstituent/ind_niftyautolist.csv
    # https://www.niftyindices.com/IndexConstituent/nifty_low_Volatility50_Index.csv
    # https://www.niftyindices.com/IndexConstituent/ind_niftyoilgaslist.csv
    # javascript:;
    data = yf.debug_update()
    print(data)
