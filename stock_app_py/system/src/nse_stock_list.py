import os
import re
import subprocess
import pandas
import csv

from stock_app_py.utility.src.csv_checker import is_csv_html
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.utility.src.yaml_parser import read_config, save_config
from stock_app_py.system.base.system import System
from stock_app_py.system.interface.system_if import RetVal


class NseStockList(System):
    def __init__(
        self,
        indicator_config_file: str,
        selected_stocks_config_file: str,
        parameter: dict,
        command_handler: object,
        name="",
    ) -> None:
        """Download the indexes from nse. Updated the selected stock config
        Nifty50:
        - ABB
        - BEL

        e.g. nsestocklist --do get, nsestocklist --do update
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
            "surveillance_stocks": self.__get_stocks_in_surveillance,
        }
        self.index_stock_map = {}

    def __get(self) -> RetVal:
        """Return dict with selected stocks.
        Returns:
            RetVal: selected stock config
        """
        self.index_stock_map = read_config(
            f'{self.parameter["config_dir"]}/index_stock.yaml'
        )
        return RetVal(obj=self.index_stock_map, obj_as_str="dict of stocks", errors="")

    def __update(self) -> RetVal:
        """Send query and fetch stocks based on indexes and then updated the
        selected_stocks_config_file.
        """
        df = pandas.read_csv(
            f'{self.parameter["config_dir"]}/{self.parameter["index_csv"]}'
        )
        err = ""

        # download the csv using wget
        for _, row in df.iterrows():
            try:
                index_key = row["INDEX \n"].lower()
                index_key = re.sub(r"[^a-zA-Z0-9]", "", index_key)
                key = f"ind_{index_key}list.csv"
                if not self.__req_download(key):
                    key = f"ind_{index_key}_list.csv"
                    self.__req_download(key)
            except Exception as e:
                err += f"{index_key} -> {e.args()}"
        self.__create_yaml()
        return RetVal(obj={}, obj_as_str="update index list", errors="")

    def __get_stocks_in_surveillance(self) -> list:
        """List all the stocks are in surveillance. No trade for surveillance stocks
        since it gets difficult to sell them when needed.

        Note: This relies on manually downloading the csv files from
        asm - https://www.nseindia.com/regulations/additional-surveillance-measure
        esm - https://www.nseindia.com/regulations/enhanced-surveillance-measure-esm
        gsm - https://www.nseindia.com/regulations/graded-surveillance-measure

        Returns:
            list: list of all in surveillance stocks
        """
        asm_surveillance = pandas.read_csv(
            f'{self.parameter["config_dir"]}/asm.csv', encoding="utf-8"
        )
        esm_surveillance = pandas.read_csv(
            f'{self.parameter["config_dir"]}/esm.csv', encoding="ISO-8859-1"
        )
        gsm_surveillance = pandas.read_csv(
            f'{self.parameter["config_dir"]}/gsm.csv', encoding="utf-8"
        )
        ret = (
            asm_surveillance["SYMBOL \n"].tolist()
            + esm_surveillance["Symbol"].tolist()
            + gsm_surveillance["SYMBOL \n"].tolist()
        )
        ret = [x for x in ret if str(x) != "nan"]
        return RetVal(obj=ret, obj_as_str="surveillance stock list", errors="")

    def __create_yaml(self):
        """Creates a stock config yaml based on the index csvs present in config_dir.
        Delete the index csvs after yaml is generated.
        e.g.
        nifty50:
            -ABB
            -BEL
        nifty100:
            -TATA
        Returns:
            RetVal: selected stock config
        """
        # create selected stocks config file
        ret = {}
        files = os.listdir(self.parameter["config_dir"])
        for file in files:
            try:
                if "ind_nifty" in file and ".csv" in file:
                    index = (file.split("_")[1]).split(".")[0][:-4]
                    df = pandas.read_csv(
                        os.path.join(self.parameter["config_dir"], file)
                    )
                    ret[index] = df["Symbol"].to_list()
            except Exception as e:
                print("ERROR: ", self.__get_stocks_in_surveillance.__name__, e.args)
                continue
        save_config(ret, f'{self.parameter["config_dir"]}/index_stock.yaml')
        self.index_stock_map = ret

        # delete exisiting index csvs, no need to store the csvs now
        files = os.listdir(self.parameter["config_dir"])
        for file in files:
            if "ind_nifty" in file and ".csv" in file:
                os.remove(os.path.join(self.parameter["config_dir"], file))

        # update the selected stock yaml
        selected_stock = self.selected_stocks_config
        for index, stocks in self.index_stock_map.items():
            # TODO Check how to add index list
            for stock in stocks:
                if stock not in selected_stock["stock"]:
                    selected_stock["stock"].append(stock)
        selected_stock["stock"].sort()
        save_config(
            selected_stock, f'{self.parameter["config_dir"]}/selected_stocks.yaml'
        )

    def __req_download(self, key: str):
        try:
            prefix = "https://www.niftyindices.com/IndexConstituent/"
            command = [
                "wget",
                "--user-agent=Mozilla/5.0",
                "--content-disposition",
                "-P",
                self.parameter["config_dir"],
                prefix + key,
            ]
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            _, stderr = process.communicate()
            file_path = f'{os.path.join(self.parameter["config_dir"], key)}'
            if is_csv_html(file_path=file_path):
                os.remove(file_path)
                return False
            else:
                return True
        except Exception as e:
            return False

    def debug(self):
        return self.__update()


if __name__ == "__main__":
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    yf = NseStockList(
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
    data = yf.debug()
    print(data)
