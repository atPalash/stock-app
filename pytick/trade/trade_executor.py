from datetime import datetime
import json
import pandas as pd

COLUMNS = ['datetime', 'ticker', 'side', 'entry', 'stop', 'profit']


class TradeExecutor:
    def __init__(self, redis, user_id, query, db_data=None):
        self.redis = redis
        self.user_id = user_id
        self.query = query  # Full query string as field
        self.trade_key = f"trade:{user_id}"
        self.db_data = db_data or {}  # Store portfolio in trades field

    def get_portfolio(self) -> pd.DataFrame:
        """Get this query's portfolio DataFrame from db_data portfolio field"""
        portfolio_records = self.db_data.get('portfolio', [])

        if not portfolio_records:
            return pd.DataFrame(columns=COLUMNS)
        else:
            all_records = []
            for record in portfolio_records:
                all_records.append(record)
            # Convert list of records back to DataFrame
            return pd.DataFrame(all_records)

    def _save_portfolio(self, portfolio_df):
        """Save portfolio to db_data portfolio field as list of records"""
        self.db_data['portfolio'] = portfolio_df.to_dict('records')

    def open_trade(self, ticker, direction, entry_price, initial_sl=None, datetime=None):
        """Add new row to portfolio (skip if already exists)"""
        portfolio_df = self.get_portfolio()

        # Don't open if already exists
        if ticker in portfolio_df['ticker'].values:
            return False

        # Calculate initial SL if not provided
        if initial_sl is None:
            initial_sl = entry_price

        # Use provided datetime or default to now
        if datetime is None:
            datetime = datetime.now().isoformat()

        new_row = {}
        for col in COLUMNS:
            if col == 'datetime':
                new_row[col] = datetime
            elif col == 'ticker':
                new_row[col] = ticker
            elif col == 'side':
                new_row[col] = direction
            elif col == 'entry':
                new_row[col] = entry_price
            elif col == 'stop':
                new_row[col] = round(float(initial_sl), 2)
            elif col == 'profit':
                new_row[col] = 0.0
            else:
                raise ValueError(f"Unknown column {col}")

        portfolio_df = pd.concat(
            [portfolio_df, pd.DataFrame([new_row])], ignore_index=True)

        # Save back to db_data
        self._save_portfolio(portfolio_df)
        return True

    def close_trade(self, ticker, exit_price, reason):
        """Close trade, calculate PnL, and remove from portfolio"""
        portfolio_df = self.get_portfolio()
        trade = portfolio_df[portfolio_df['ticker'] == ticker]

        if trade.empty:
            return None

        trade_row = trade.iloc[0]

        if trade_row['side'] == 'buy':
            # 1 share assumed
            pnl = (exit_price - trade_row['entry']) * 1
        else:
            pnl = (trade_row['entry'] - exit_price) * 1

        # Build trade summary before removing
        closed_trade = {
            'ticker': ticker,
            'side': trade_row['side'],
            'entry': trade_row['entry'],
            'exit_price': exit_price,
            'current_sl': trade_row['current_sl'],
            'pnl': pnl,
            'reason': reason
        }

        # Remove trade from portfolio
        portfolio_df = portfolio_df[portfolio_df['ticker'] != ticker]

        # Save back to db_data
        self._save_portfolio(portfolio_df)

        return closed_trade

    def update_col(self, ticker, col, value):
        """Update stop loss for a trade (for rolling stops)"""
        portfolio_df = self.get_portfolio()

        if ticker not in portfolio_df['ticker'].values:
            return False

        if col == 'profit':
            # Also update current SL for gain column
            entry_price = portfolio_df.loc[portfolio_df['ticker']
                                           == ticker, 'entry'].values[0]
            direction = portfolio_df.loc[portfolio_df['ticker']
                                         == ticker, 'side'].values[0]
            if direction == 'buy':
                profit = value - entry_price
            else:
                profit = entry_price - value
            portfolio_df.loc[portfolio_df['ticker']
                             == ticker, 'profit'] = round(float(profit), 2)
        else:
            portfolio_df.loc[portfolio_df['ticker']
                             == ticker, col] = round(float(value), 2)
        self._save_portfolio(portfolio_df)
        return True

    def get_open_trades(self):
        """Get list of all open trades"""
        portfolio_df = self.get_portfolio()
        return portfolio_df.to_dict('records') if not portfolio_df.empty else []
