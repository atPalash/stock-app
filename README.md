# stock-app
C++ python stock-app

# podman commands
podman run -dit -v /home/palash/stock-app/configuration:/home/palash/app/configuration --network=host --name stock-app-pyserver stock-app-pyserver:latest

# test query
```
Feature: v2
Scenario:Nifty 100 mover
Given stocks from index nifty100
When let changeEma10 = change in 30 day close ema 10
Then get tickers with changeEma10 > 0.1
When let close = latest in 1 day close
* let ma150 = latest in 1 day close ma 150
* let ma200 = latest in 1 day close ma 200
* let ma50 = latest in 1 day close ma 50
* let rateMa200 = rate in 60 day close ma 200
* let wk52Low = minimum in 52 week close
* let wk52High = maximum in 52 week close
Then get tickers with close > ma50
* get tickers with close > ma150
* get tickers with close > ma200
* get tickers with ma50 > ma150
* get tickers with ma150 > ma200
* get tickers with ma50 > 200
* get tickers with close > 1.25 * wk52Low
* get tickers with close > 0.75 * wk52High
* get tickers with rateMa200 > 0
```

# ngrok domain
palashhalder1988
`ngrok http --domain=tight-strongly-liger.ngrok-free.app 8087`
