import pandas

from pytick.utility.utility import RetVal


COLUMNS = ['ticker', 'side', 'entry', 'entry_time', 'entry_stop',
           'current_time', 'current_price', 'current_stop', 'profit', 'rmulti']


class TradeHandler:
    def __init__(self):
        self.open_df = pandas.DataFrame(columns=COLUMNS)
        self.close_df = pandas.DataFrame(columns=COLUMNS)

    def do_trade(self, ticker, side, price, time, stop_per) -> RetVal:
        # If no existing trade, open new one with initial stop loss
        if ticker not in self.open_df['ticker'].values and side in ['buy', 'sell']:
            stop = price * \
                (1 - stop_per / 100) if side == 'buy' else price * \
                (1 + stop_per / 100)
            stop = round(stop, 2)
            return self.__open_trade(ticker, side, price, time, stop)

        # Update existing trade with new price and time, and adjust stop if price moving in favorable direction
        if ticker in list(self.open_df['ticker']):
            idx = self.open_df.index[self.open_df['ticker'] == ticker][0]
            previous_price = self.open_df.at[idx, 'current_price']
            previous_stop = self.open_df.at[idx, 'current_stop']
            trade_side = self.open_df.at[idx, 'side']

            self.open_df.at[idx, 'current_time'] = time
            self.open_df.at[idx, 'current_price'] = price
            if trade_side == 'buy':
                if price > previous_price:
                    stop = price * (1 - stop_per / 100)
                    stop = round(stop, 2)
                    self.open_df.at[idx, 'current_stop'] = max(
                        previous_stop, stop)
                self.open_df.at[idx, 'profit'] = round(self.open_df.at[idx, 'current_stop'] - \
                    self.open_df.at[idx, 'entry'], 2)
            elif trade_side == 'sell':
                if price < previous_price:
                    stop = price * (1 + stop_per / 100)
                    stop = round(stop, 2)
                    self.open_df.at[idx, 'current_stop'] = min(
                        previous_stop, stop)
                self.open_df.at[idx,
                                'profit'] = round(self.open_df.at[idx, 'entry'] - self.open_df.at[idx, 'current_stop'], 2)

            rmulti = self.open_df.at[idx, 'profit'] / \
                abs(self.open_df.at[idx, 'entry'] -
                    self.open_df.at[idx, 'entry_stop'])
            self.open_df.at[idx, 'rmulti'] = round(rmulti, 2)
            current_stop = self.open_df.at[idx, 'current_stop']
            # Check if stop loss hit and close trade if needed
            if trade_side == 'buy' and price < current_stop:
                return self.__close_trade(ticker, price, time)
            if trade_side == 'sell' and price > current_stop:
                return self.__close_trade(ticker, price, time)

            return RetVal(status=True, message="Trade updated")
        return RetVal(status=True, message="Nothing to update")

    def __open_trade(self, ticker, side, entry_price, entry_time, entry_stop) -> RetVal:
        try:
            new_trade = {
                'ticker': ticker,
                'side': side,
                'entry': entry_price,
                'entry_time': entry_time,
                'entry_stop': entry_stop,
                'current_time': entry_time,
                'current_price': entry_price,
                'current_stop': entry_stop,
                'profit': 0.0,
                'rmulti': 0.0
            }
            new_trade_df = pandas.DataFrame([new_trade])
            self.open_df = pandas.concat(
                [self.open_df, new_trade_df], ignore_index=True)
            return RetVal(status=True, message="Trade opened")
        except Exception as e:
            return RetVal(status=False, message=f"Error opening trade: {str(e)}")

    def __close_trade(self, ticker, current_price, current_time) -> RetVal:
        try:
            if ticker not in self.open_df['ticker'].values:
                return RetVal(status=False, message="Trade does not exist")

            mask = (
                (self.open_df['ticker'] == ticker) &
                (self.open_df['current_price'] == current_price) &
                (self.open_df['current_time'] == current_time)
            )
            matching_indices = self.open_df.index[mask]
            if not matching_indices.empty:
                closed_trade = self.open_df.loc[matching_indices[0]].copy()
                self.close_df = pandas.concat(
                    [self.close_df, closed_trade.to_frame().T], ignore_index=True)
                self.open_df = self.open_df.drop(matching_indices[0])
                return RetVal(status=True, message="Trade closed")
            else:
                return RetVal(status=True, message="Should not happen")
        except Exception as e:
            return RetVal(status=False, message=f"Error closing trade: {str(e)}")

    def get_open_trades(self):
        return self.open_df

    def get_closed_trades(self):
        return self.close_df
