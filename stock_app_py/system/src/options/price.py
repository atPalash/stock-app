import logging
import numpy as np
import pandas
from blackscholes import BlackScholesCall, BlackScholesPut

from stock_app_py.system.interface.system_if import RetVal


def calculate_volatility(ohlc: pandas.DataFrame, trading_days=252) -> float:
    """Calculate annualised volatility for the given data frame.

    Args:
        ohlc (pandas.DataFrame): ohlc data for a ticker
        trading_days (int, optional): Total trading days in a year. Defaults to 252.

    Returns:
        float: volatility
    """
    if trading_days < 0:
        return 0
    data = ohlc[["Date", "Close"]].copy()  # Use copy to avoid SettingWithCopyWarning
    data["logRelativePrice"] = np.log(data["Close"] / data["Close"].shift(1))

    # Remove the first NA value from the calculation (created by shift)
    volatility = data["logRelativePrice"].std(skipna=True)

    return volatility * np.sqrt(trading_days)


def calculate_option_prices(
    current_stock_price, strike_price, days_to_expiry, annual_volatility, r=0.07, q=0
):
    """
    Calculate the Black-Scholes option prices for European call and put
    options using the 'blackscholes' package.

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
    if days_to_expiry < 0:
        return (0, 0)
    # Creating instances of BlackScholesCall and BlackScholesPut
    call_option = BlackScholesCall(
        S=current_stock_price,
        K=strike_price,
        T=days_to_expiry / 252,
        r=r,
        sigma=annual_volatility,
        q=q,
    )
    put_option = BlackScholesPut(
        S=current_stock_price,
        K=strike_price,
        T=days_to_expiry / 252,
        r=r,
        sigma=annual_volatility,
        q=q,
    )

    # Get call and put prices
    call_price = call_option.price()
    put_price = put_option.price()

    return call_price, put_price


def future_stock_price(ohlc: pandas.DataFrame, period_in_days: int, std_dev=1) -> tuple:
    """Assume price of stock when the underlying moves by std_dev

    Args:
        ohlc (pandas.DataFrame): OHLC of underlying
        period_in_days (int): number of days to make the move
        std_dev (int, optional): Deviation from price. Defaults to 1.

    Returns:
        tuple: upper, lower price of underlying
    """
    if period_in_days < 0:
        return (0, 0)
    volatility = calculate_volatility(ohlc=ohlc, trading_days=period_in_days)
    current_price = ohlc.iloc[-1]["Close"]
    price_up = current_price * np.exp(std_dev * volatility)
    price_low = current_price * np.exp(-std_dev * volatility)
    return (price_up, price_low)
