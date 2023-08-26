class TradingViewChart {
    #height
    #width
    #chart
    #slide
    constructor(height, width) {
        this.#height = height
        this.#width = width
        this.#chart = null
        this.#slide = null
    }

    setHeightWidth(height, width) {
        this.#slide.style.width = `${width}px`
        this.#slide.style.height = `${height}px`
        this.#chart.applyOptions({ height: height, width: width });
    }
    async plotCandle(slideData) {
        var query_ohlc = { "query": `webserver --ticker ${slideData.symbol} --interval ${slideData.interval} --do get --indicator ohlc --n ${slideData.n}` }
        var resp_ohlc = await apiPost("ohlc",query_ohlc);
        resp_ohlc = this.#extractOhlc(resp_ohlc, slideData.symbol)
        const slide = document.createElement('div');
        slide.classList.add(`tv-chart`);
        slide.setAttribute("id", `${slideData.symbol}`)
        slide.style.display = 'block';
        slide.style.height = `${this.#height}px`
        slide.style.width = `${this.#width}px`
        const intervalsWithOutTime = ["month", "week", "day"]
        const tvChart = LightweightCharts.createChart(slide, {
            // autoSize: true
            height: this.#height,
            width: this.#width,
            timeScale: {
                timeVisible: !intervalsWithOutTime.includes(slideData.interval),
                timeFormat: '%h:%m',
            },
        });

        const tvSeries = tvChart.addCandlestickSeries();
        tvSeries.setData(resp_ohlc);

        // go through each desired indicator and plot them
        for (let key in slideData.indicators) {
            var indicator = slideData.indicators[key]
            switch(indicator['type']) {
                case 'ema':
                    var query = { "query": `webserver --ticker ${slideData.symbol} \
                    --interval ${slideData.interval} --do get --indicator ema \
                    --window ${indicator["window"]} --n ${slideData.n}`}
                    var resp = await apiPost("ohlc",query);
                    var series = this.#extractIndicatorValue(resp, slideData.symbol)
                    const chartSeries = tvChart.addLineSeries({ color: indicator['color'], lineWidth: 1 });
                    chartSeries.setData(series);
                    break;
                case 'volume':
                    var series = resp_ohlc.map(item => {
                        return { time: item.time, value: item.volume, color: item.open > item.close ? 'red' : 'green' };
                    });
                    const volumeSeries = tvChart.addHistogramSeries({
                        color: '#26a69a',
                        priceFormat: {
                            type: 'volume',
                        },
                        priceScaleId: ''
                    });
                    volumeSeries.priceScale().applyOptions({
                        // set the positioning of the volume series
                        scaleMargins: {
                            top: 0.8, // highest point of the series will be 70% away from the top
                            bottom: 0,
                        },
                    });
                    volumeSeries.setData(series)
                    break
                default:
                    console.log("Indicator not avaialable")
            }
        }

        // go throught each desired scanner and plot signals
        var markers = []
        for (let key in slideData.scanners) {
            var scanner = slideData.scanners[key]
            switch(scanner['type']) {
                case 'macd_divergence':
                    var query_macd_div = { "query": `webserver --ticker ${slideData.symbol} \
                    --interval ${slideData.interval} --do get --indicator macdhistdivergencescan \
                    --n ${scanner["n"]} --window ${scanner["window"]}` }
                    var resp_macd_div = await apiPost("ohlc",query_macd_div);
                    var signals_macd_div = this.#extractSignal(resp_macd_div, slideData.symbol, 
                        {"buyColor": scanner["buyColor"], "sellColor": scanner["sellColor"]})
                    
                    markers.push(...signals_macd_div)
                    tvSeries.setMarkers(markers);
                    break;
                default:
                    console.log("Scanner not avaialable")
            }
        }
        this.#chart = tvChart
        this.#slide = slide
        return slide
    }

    #extractOhlc(data, symbol) {
        var ohlc = []
        for (const [timestamp, map] of Object.entries(data[symbol])) {
            var row = {
                'time': convertToUtc(timestamp),
                'open': map['Open'],
                'high': map['High'],
                'low': map['Low'],
                'close': map['Close'],
                'volume': map['Volume']
            }
            ohlc.push(row)
        }
        return ohlc
    }

    #extractIndicatorValue(data, symbol) {
        var values = []
        for (const [time, value] of Object.entries(JSON.parse(data[symbol]))) {
            var row = {
                'time': convertToUtc(time),
                'value': value
            }
            values.push(row)
        }
        return values
    }

    #extractSignal(data, symbol, options) {
        var signals = []
        for (const [time, value] of Object.entries(JSON.parse(data[symbol]))) {
            if (value === 1) {
                var row = {
                    'time': convertToUtc(time),
                    'position': 'belowBar',
                    'color': options["buyColor"],
                    'shape': 'arrowUp',
                }
                signals.push(row)
            }
            else if (value === -1) {
                var row = {
                    'time': convertToUtc(time),
                    'position': 'aboveBar',
                    'color': options["sellColor"],
                    'shape': 'arrowDown',
                }
                signals.push(row)
            }
        }
        return signals
    }
}
