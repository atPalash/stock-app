import pandas as pd

# import mplfinance as mpf

import matplotlib.dates as mdates

colors = {
    "candle_up": "green",
    "candle_down": "red",
    "ema": "blue",
    "macd_fast": "red",
    "macd_signal": "red",
    "macd_histogram": "red",
}


def plot(**kwargs):
    try:
        ohlc = kwargs["ohlc"]

        additions = []
        for key in colors.keys():
            if key in kwargs:
                plot = None
                if "macd_histogram" in key:
                    plot = mpf.make_addplot(
                        kwargs[key],
                        type="bar",
                        width=0.7,
                        panel=1,
                        color=colors[key],
                        alpha=1,
                        secondary_y=True,
                    )
                elif "macd_signal" in key or "macd_fast" in key:
                    plot = (mpf.make_addplot(kwargs[key], panel=1, color=colors[key]),)
                else:
                    plot = mpf.make_addplot(kwargs[key], color=colors[key])
                additions.append(plot)

        mpf.plot(
            data=ohlc,
            type="candle",
            addplot=additions,
            title=kwargs.get("stock", "No title"),
            volume=kwargs.get("volume", False),
            style="yahoo",
        )
    except Exception as e:
        print(e.args)
        raise
