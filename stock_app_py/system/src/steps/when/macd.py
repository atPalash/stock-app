from stock_app_py.utility.src.steps import when
from stock_app_py.system.src.steps.when import aggregator
import stock_app_py.system.src.command_handler as executor

import pandas


@when
def shows_macd_divergence(
    selected_stocks_yaml,
    indicator_config_yaml,
    ticker,
    groups,
    lookback_window: int = -1,
):
    try:
        command_handler = executor.CommandHandler(
            selected_stocks_yaml, indicator_config_yaml
        )
        if len(groups) == 7:
            (
                interval,
                ohlc,
                window,
                fastperiod,
                slowperiod,
                signalperiod,
                tickcount,
            ) = groups
        elif len(groups) == 4:
            interval, ohlc, window, tickcount = groups
            fastperiod = 12
            slowperiod = 26
            signalperiod = 9
        else:
            raise ("Valid parameters not found")

        macdhist_query = f"talibquery --ticker {ticker} --interval {interval} --do get \
                    --indicator macdhist --fastperiod {fastperiod} \
                    --slowperiod {slowperiod} --signalperiod {signalperiod} \
                    --n 1000 --latest 0 --window {window} \
                    --ohlc {ohlc.capitalize()}"

        ticker_df = command_handler.execute(macdhist_query, is_rest=False).obj
        window = int(window)

        def logic(df: pandas.DataFrame):
            roll_window_start_index = df.index.stop - window
            roll_window = df.loc[roll_window_start_index : df.index.stop]
            window_macdhist = roll_window["macdhist"]
            window_macdhist_min = window_macdhist.min()
            window_macdhist_max = window_macdhist.max()

            divergence = 0
            # Check if the data has divergence in the samples, ie machist values oscillates
            if window_macdhist_min < 0 and window_macdhist_max > 0:
                window_macdhist_min_index = window_macdhist[
                    window_macdhist == window_macdhist_min
                ].index[0]
                window_macdhist_max_index = window_macdhist[
                    window_macdhist == window_macdhist_max
                ].index[0]

                # Check bullish divergence. The two mins must be on both sides
                # of the zero-cross. Start with finding the first min on left of
                # max.
                if window_macdhist_min_index < window_macdhist_max_index:
                    sub_window = roll_window.loc[
                        window_macdhist_max_index : df.index.stop
                    ]
                    sub_window_macdhist = sub_window["macdhist"]
                    sub_window_macdhist_min = sub_window_macdhist.min()
                    sub_window_macdhist_max = sub_window_macdhist.max()

                    # Check if we get second min after zero-cross. Second
                    # min on right of max
                    if sub_window_macdhist_min < 0 and sub_window_macdhist_max > 0:
                        sub_window_macdhist_min_index = sub_window_macdhist[
                            sub_window_macdhist == sub_window_macdhist_min
                        ].index[0]

                        # check for divergence condition
                        priceA = roll_window[ohlc.capitalize()].loc[
                            window_macdhist_min_index
                        ]
                        priceC = roll_window[ohlc.capitalize()].loc[
                            sub_window_macdhist_min_index
                        ]
                        macdhistA = window_macdhist_min
                        macdhistC = sub_window_macdhist_min
                        if priceA > priceC and macdhistA < macdhistC:
                            divergence = 1

                # Check bearish divergence. The two maxs must be on both the
                # sides of the zero-cross. First start with finding the
                # first max is left of min
                if window_macdhist_min_index > window_macdhist_max_index:
                    sub_window = roll_window.loc[
                        window_macdhist_min_index : df.index.stop
                    ]
                    sub_window_macdhist = sub_window["macdhist"]
                    sub_window_macdhist_min = sub_window_macdhist.min()
                    sub_window_macdhist_max = sub_window_macdhist.max()

                    # Check if we get second max after zero-cross. the 2nd
                    # max is right of min.
                    if sub_window_macdhist_min < 0 and sub_window_macdhist_max > 0:
                        sub_window_macdhist_max_index = sub_window_macdhist[
                            sub_window_macdhist == sub_window_macdhist_max
                        ].index[0]

                        # check for divergence condition
                        priceA = roll_window[ohlc.capitalize()].loc[
                            window_macdhist_max_index
                        ]
                        priceC = roll_window[ohlc.capitalize()].loc[
                            sub_window_macdhist_max_index
                        ]
                        macdhistA = window_macdhist_max
                        macdhistC = sub_window_macdhist_max
                        if priceA < priceC and macdhistA > macdhistC:
                            divergence = -1

            return {
                "ticker": ticker,
                "interval": interval,
                "condition": divergence != 0,
                "signal": divergence,
                "exception": None,
            }

        return aggregator.get_result(
            lookback_window=lookback_window, logic=logic, ticker_df=ticker_df
        )
    except Exception as e:
        return {"ticker": ticker, "exception": e.args}
