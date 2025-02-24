import logging
import numpy as np
import pandas
from blackscholes import BlackScholesCall, BlackScholesPut

from stock_app_py.system.interface.system_if import RetVal


def calculate_volatility(ohlc: pandas.DataFrame, trading_days: int) -> float:
    """Calculate volatility for the given data frame depending on the trading days.

    Args:
        ohlc (pandas.DataFrame): ohlc data for a ticker
        trading_days (int, optional): Total trading days in a year.

    Returns:
        float: volatility
    """
    if trading_days <= 0:
        return 0
    data = ohlc[["Date", "Close"]].copy()  # Use copy to avoid SettingWithCopyWarning
    data["logRelativePrice"] = np.log(data["Close"] / data["Close"].shift(1))

    # Remove the first NA value from the calculation (created by shift)
    daily_volatility = data["logRelativePrice"].std(skipna=True)

    return daily_volatility * np.sqrt(trading_days)


def future_stock_price(
    current_price: float, period_in_days: int, volatility: float, std_dev=1
) -> tuple:
    """Assume price of stock when the underlying moves by std_dev

    Args:
        ohlc (pandas.DataFrame): OHLC of underlying
        period_in_days (int): number of days to make the move
        std_dev (int, optional): Deviation from price. Defaults to 1.

    Returns:
        tuple: upper, lower price of underlying
    """
    if period_in_days <= 0:
        return (0, 0)
    volatility = volatility
    current_price = current_price
    price_up = current_price * np.exp(std_dev * volatility)
    price_low = current_price * np.exp(-std_dev * volatility)
    return (price_up, price_low)


def calculate_option_prices(S, K, T, r, sigma, q):
    """
    Calculate the Black-Scholes option prices for European call and put options using the 'blackscholes' package.

    Parameters:
    S : float - current stock price
    K : float - strike price of the option
    T : float - time to maturity (in years)
    r : float - risk-free interest rate (annual as a decimal)
    sigma : float - volatility of the underlying stock (annual as a decimal)
    q : float - annual dividend yield (as a decimal)

    Returns:
    tuple - (call price, put price)
    """
    # Creating instances of BlackScholesCall and BlackScholesPut
    call_option = BlackScholesCall(S=S, K=K, T=T, r=r, sigma=sigma, q=q)
    put_option = BlackScholesPut(S=S, K=K, T=T, r=r, sigma=sigma, q=q)

    # Get call and put prices
    call_price = round(call_option.price(), 2)
    put_price = round(put_option.price(), 2)

    return call_price, put_price
