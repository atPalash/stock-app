class TradingViewChart {
    #height
    #width
    #chart
    constructor(height, width) {
        this.#height = height
        this.#width = width
        this.#chart = null
    }

    setHeightWidth(height, width) {
        this.#chart.applyOptions({ height: height, width: width });
    }
    async plotCandle(slideData) {
        var query_ohlc = { "query": `webserver --ticker ${slideData.symbol} --interval ${slideData.interval} --do get --indicator ohlc --n ${slideData.n}` }
        var resp_ohlc = await apiCall(query_ohlc);
        resp_ohlc = this.#extractOhlc(resp_ohlc, slideData.symbol)
        const slide = document.createElement('div');
        slide.classList.add(`tv-chart`);
        slide.setAttribute("id", `${slideData.symbol}`)
        slide.style.display = 'block';
        slide.style.height = `${this.#height}px`
        slide.style.width = `${this.#width}px`

        const tvChart = LightweightCharts.createChart(slide, {
            // autoSize: true
            height: this.#height,
            width: this.#width
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
                    var resp = await apiCall(query);
                    var series = this.#extractIndicatorValue(resp, slideData.symbol)
                    const chartSeries = tvChart.addLineSeries({ color: indicator['color'], lineWidth: 1 });
                    chartSeries.setData(series);
                    break;
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
                    var resp_macd_div = await apiCall(query_macd_div);
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