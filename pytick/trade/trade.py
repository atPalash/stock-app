import redis

from pytick.utility.utility import RetVal
from pytick.utility.convo_store import ConvoStore
from pytick.dataframe.dataframe import DataFrameHandler
from pytick.dataframe.notification import NotificationHandler
from pytick.trade.trade_executor import TradeExecutor
from pytick.utility.utility import get_logger, read_config, read_file
logger = get_logger(__file__)


class TradeHandler:
    def __init__(self, data_handler: DataFrameHandler, notification_handler: NotificationHandler,
                 interval_translation: dict, interval_seconds: dict, convo_store: ConvoStore):
        self.data_handler = data_handler
        self.notification_handler = notification_handler
        self.interval_translation = interval_translation
        self.interval_seconds = interval_seconds
        self.convo_store = convo_store

    def do_trade(self, user, query, db_data, result) -> RetVal:
        """Execute trade logic: open new trades, close when SL hit, send summary"""
        try:
            # Initialize executor with query as field and db_data for portfolio storage
            executor = TradeExecutor(
                redis=self.convo_store.redis,
                user_id=user.id,
                query=query,
                db_data=db_data
            )

            # Extract current tickers from results
            current_tickers = {'buy': set(), 'sell': set()}
            for result_dict in result.data.get('results', []):
                for direction, tickers in result_dict.items():
                    if direction in ['buy', 'sell']:
                        current_tickers[direction].update(tickers)

            opened = []
            closed = []
            stop_loss_percent = db_data.get('stop_loss_percent', 5)
            use_rolling_stop = db_data.get(
                'rolling_stop', True)  # Default: rolling SL
            # OPEN new trades on signals
            for direction in ['buy', 'sell']:
                for ticker in current_tickers[direction]:
                    try:
                        # Get current price (always use 5m for real-time pricing)
                        price_df = self.data_handler.get_tables(
                            tickers=[ticker], interval='5m'
                        ).get('data', {}).get(ticker)

                        if price_df is not None and not price_df.empty:
                            entry_price = price_df['close'].iat[-1]
                            # Get entry time from OHLC data and convert to string
                            entry_time = price_df['datetime'].iat[-1].isoformat()

                            # Calculate initial SL
                            if direction == 'buy':
                                initial_sl = entry_price * \
                                    (1 - stop_loss_percent / 100)
                            else:  # sell
                                initial_sl = entry_price * \
                                    (1 + stop_loss_percent / 100)

                            if executor.open_trade(ticker, direction, entry_price, initial_sl, entry_time):
                                opened.append({
                                    'ticker': ticker,
                                    'side': direction,
                                    'price': entry_price,
                                    'time': entry_time
                                })
                                logger.info(
                                    f"Trade opened: {ticker} {direction} @ {entry_price} at {entry_time}")
                    except Exception as e:
                        logger.warning(
                            f"Failed to open trade for {ticker}: {e}")

            # CLOSE trades: ONLY if stop-loss is hit (rolling or hard stop)
            for trade in executor.get_open_trades():
                ticker = trade['ticker']
                entry_price = trade['entry']

                try:
                    # Get current price (always use 5m for real-time pricing)
                    price_df = self.data_handler.get_tables(
                        tickers=[ticker], interval='5m'
                    ).get('data', {}).get(ticker)

                    if price_df is None or price_df.empty:
                        continue

                    current_price = price_df['close'].iat[-1]

                    # Stop-loss: rolling or hard
                    if trade['side'] == 'buy':
                        if use_rolling_stop:
                            # Rolling SL: move stop up if price goes up
                            rolling_sl = current_price * \
                                (1 - stop_loss_percent / 100)
                            entry_sl = entry_price * \
                                (1 - stop_loss_percent / 100)
                            current_sl = max(rolling_sl, entry_sl)
                            # Update SL in portfolio
                            executor.update_col(
                                ticker, 'stop', current_sl)
                        else:
                            # Hard SL: fixed at entry
                            current_sl = entry_price * \
                                (1 - stop_loss_percent / 100)
                        should_close = current_price <= current_sl

                    else:  # sell
                        if use_rolling_stop:
                            # Rolling SL: move stop down if price goes down
                            rolling_sl = current_price * \
                                (1 + stop_loss_percent / 100)
                            entry_sl = entry_price * \
                                (1 + stop_loss_percent / 100)
                            current_sl = min(rolling_sl, entry_sl)
                            # Update SL in portfolio
                            executor.update_col(
                                ticker, 'stop', current_sl)
                        else:
                            # Hard SL: fixed at entry
                            current_sl = entry_price * \
                                (1 + stop_loss_percent / 100)
                        should_close = current_price >= current_sl
                    executor.update_col(ticker, 'profit', current_price)
                    if should_close:
                        closed_trade = executor.close_trade(
                            ticker, current_price, 'stop')
                        if closed_trade:
                            closed.append(closed_trade)
                            logger.info(
                                f"Trade closed: {ticker} SL hit @ {current_price} | PnL: ₹{closed_trade['pnl']:.0f}")
                except Exception as e:
                    logger.warning(
                        f"Failed to process trade for {ticker}: {e}")

            # Update stored data with current results
            # current_results = result.data.get('results', [])
            # db_data['results'] = current_results
            # self.convo_store.subscribe_query(
            #     user.id, query, db_data, 'trade')
            return RetVal(status=True, message="Trade execution completed",
                          data={'portfolio': executor.get_portfolio().to_dict(orient='records'),
                                'opened': opened, 'closed': closed})
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return RetVal(status=False, message="Trade execution failed",
                          errors=[str(e)], data={})
