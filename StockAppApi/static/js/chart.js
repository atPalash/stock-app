class TradingViewChart {
    #row
    #col
    #height
    #width
    #slides;
    #parentContainer;
    #slideClassName;
    #controls;
    constructor(row, col, height, width, controls) {
        this.#row = row
        this.#col = col
        this.#height = height
        this.#width = width

        this.#slides = []
        this.#parentContainer = document.getElementById(`gallery-container-${this.#row}-${this.#col}`);
        this.#slideClassName = "gallery-slide"
        this.#controls = controls
    }

    setControls(controls) {
        this.#controls = controls
    }

    async show(redraw=false) {
        // here sending a dummy ticker so that in server side we don't do repeated calls to
        // get ticker list
        // var tickers = await apiCall({ "query": `webserver --ticker all --do get --indicator tickers` });
        this.#slides = Array(this.#controls["tickers"].length)
        this.#slides.fill(null)
        await this.showSlide(this.#controls["currentSlideIndex"], redraw)
    }

    async showSlide(redraw=false) {
        var currentSlideIndex = this.#controls["currentSlideIndex"]
        if(redraw) {
            this.clearAllSlides()
        }
        this.#slides.forEach(slide => {
            if(slide != null) {
                slide.style.display = 'none';
            }
        });

        if (this.#slides[currentSlideIndex] == null) {
            var slideData = {
                symbol: this.#controls["tickers"][currentSlideIndex], interval: this.#controls["interval"], n: this.#controls["tickcount"],
                'indicators': this.#controls['indicators'], 'scanners': this.#controls["scanners"]
            }
            var slide = await this.#plotCandle(slideData)
            this.#slides[currentSlideIndex] = slide
        }
        
        this.#slides[currentSlideIndex].style.display = 'block';
    }

    clearAllSlides() {
        var elements = document.getElementsByClassName(this.#slideClassName);
        elements = [...elements]
        elements = elements.filter(element => element.id == `${this.#slideClassName}-${this.#row}-${this.#col}`)
        elements.forEach(element => {
            element.parentNode.removeChild(element);
        });

        this.#slides = Array(this.#controls["tickers"].length)
        this.#slides.fill(null)
    }

    async #plotCandle(slideData) {
        var query_ohlc = { "query": `webserver --ticker ${slideData.symbol} --interval ${slideData.interval} --do get --indicator ohlc --n ${slideData.n}` }
        var resp_ohlc = await apiCall(query_ohlc);
        resp_ohlc = this.#extractOhlc(resp_ohlc, slideData.symbol)
        const slide = document.createElement('div');
        slide.classList.add(`${this.#slideClassName}`);
        slide.setAttribute("id", `${this.#slideClassName}-${this.#row}-${this.#col}`)
        slide.innerHTML = `
              <div class="tv-chart-container" id="tv-chart-container-${this.#row}-${this.#col}">
                <div id="tv-chart-${slideData.symbol}-${this.#row}-${this.#col}" class="tv-chart"></div>
              </div>
            `;
        slide.style.display = 'none';
        this.#parentContainer.appendChild(slide);

        const tvChart = LightweightCharts.createChart(document.getElementById(`tv-chart-${slideData.symbol}-${this.#row}-${this.#col}`), {
            width: this.#width,
            height: this.#height,
        });

        const tvSeries = tvChart.addCandlestickSeries();
        tvSeries.setData(resp_ohlc);

        // go through each desired indicator and plot them
        for (let key in this.#controls["indicators"]) {
            var indicator = this.#controls["indicators"][key]
            switch(indicator['type']) {
                case 'ema':
                    var query = { "query": `webserver --ticker ${slideData.symbol} \
                    --interval ${this.#controls["interval"]} --do get --indicator ema \
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
        for (let key in this.#controls["scanners"]) {
            var scanner = this.#controls["scanners"][key]
            switch(scanner['type']) {
                case 'macd_divergence':
                    var query_macd_div = { "query": `webserver --ticker ${slideData.symbol} \
                    --interval ${this.#controls["interval"]} --do get --indicator macdhistdivergencescan \
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

var chart = null
async function renderChart(row, col, height, width, controls, redraw=false) {
    if(chart != null) {
        chart = null
    }
    chart = new TradingViewChart(row, col, height, width, controls)
    chart.show(redraw)
};

async function showChart(controls, redraw=false) {
    if(chart != null) {
        chart.setControls(controls)
        chart.showSlide(redraw)
    }
}