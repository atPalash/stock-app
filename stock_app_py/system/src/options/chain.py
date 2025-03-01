import logging
import pandas
import requests

from stock_app_py.system.src.yahoo_finance import YahooFinance
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.system.base.system import System
from stock_app_py.system.interface.system_if import RetVal


class OptionChain:
    def __init__(self) -> None:
        """Webscrap to get available option chain of stocks or index. Remeber to
        disable vpn.

        e.g.
        1. optionchain --do get --ticker ADANIPORTS
        Args:
            indicator_config_file (str): indicator configuration
            selected_stocks_config_file (str): selected stocks list
            parameter (dict): key-value pairs for setting up the query
            command_handler (object): to call other systems
            name (str, optional): Name of the query. Defaults to "".
        """
        self.url_oc: str = "https://www.nseindia.com/option-chain"
        self.url_index: str = (
            "https://www.nseindia.com/api/option-chain-indices?symbol="
        )
        self.url_stock: str = (
            "https://www.nseindia.com/api/option-chain-equities?symbol="
        )

        self.session = requests.sessions.Session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.timeout = 5
        self.session.get(self.url_oc, timeout=self.timeout)

    def requestNseOptionChain(self, ticker: str) -> dict:
        """Request nse to fetch option for a ticker.

        Args:
            ticker (str): ticker name.e.g COALINDIA

        Returns:
            dict: returns a dictionary of expiry dates and its respective strike price
            {
                <expiry>: [<strike_price>: {'CE':<data>, 'PE': <data>}]
            }
        """
        try:
            formatted_ticker = self._formatIndexSymbol(ticker)
            isIndex = ticker != formatted_ticker
            url = self.url_index if isIndex else self.url_stock
            url = url + formatted_ticker
            data = self.session.get(url=url, timeout=self.timeout)
            data = data.json()

            expiry_dates = data["records"]["expiryDates"]
            result = {key: [] for key in expiry_dates}
            for row in data["records"]["data"]:
                if "CE" in row.keys() and "PE" in row.keys():
                    result[row["expiryDate"]].append(
                        {
                            "strikePrice": row["strikePrice"],
                            "CE": row["CE"],
                            "PE": row["PE"],
                        }
                    )
            return result
        except Exception as err:
            logging.error(err)

    def _formatIndexSymbol(self, symbol: str) -> str:
        # NIFTY | FINNIFTY | BANKNIFTY | NIFTYMID50 | MIDCPNIFTY https://www.nseindia.com/api/option-chain-indices
        index_symbols = {
            "^NSEI": "NIFTY",
            "^NSEBANK": "BANKNIFTY",
            "^NSMIDCP": "MIDCPNIFTY",
            "NIFTY_FIN_SERVICE": "FINNIFTY",
            "NIFTY_MID_SELECT": "NIFTYMID50",
        }
        if symbol in index_symbols.keys():
            return index_symbols[symbol]
        return symbol


if __name__ == "__main__":
    oc = OptionChain()
    oc.requestNseOptionChain(ticker="ADANIPORTS")
