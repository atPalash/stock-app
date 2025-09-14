import yfinance as yf

def download_stock_data(ticker:str, interval:str, tz:str)->None:
    data = yf.download(
        tickers=[f"{ticker}{".NS" if tz=="Asia/Kolkata" else ""}"],
        period="max",
        interval=interval,
        progress=False,
        group_by="ticker",
        rounding=True,
        actions=True,
        threads=True,
        multi_level_index=False,
        ignore_tz=True,
        auto_adjust=True,
    )
    return data

if __name__ == "__main__":
    download_stock_data("BEL", "5m", "Asia/Kolkata")
    
'''
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    sleeps = {
            "1m": 1,
            "2m": 2,
            "5m": 5,
            "15m": 10,
            "30m": 15,
            "1d": 20,
            "1h": 25,
            "1wk": 30,
            }
    scheduler = BackgroundScheduler()
    scheduler.start()
    for interval, rep in {"1m": "*/1", "2m": "*/2"}.items():
        scheduler.add_job(
            lambda interval = interval: download_stock_data("BEL", interval, "Asia/Kolkata"),
            trigger=CronTrigger(minute=rep, day_of_week="mon-fri", timezone=pytz.timezone("Asia/Kolkata"))
        )
    try:
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
    # print(download_stock_data("BEL", "2m", "Asia/Kolkata").tail(10))

# data.to_csv("test.csv")

'''    
