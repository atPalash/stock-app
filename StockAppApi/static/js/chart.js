class TradingViewChart {
    #row
    #col
    #height
    #width
    #currentSlideIndex;
    #slides;
    #interval;
    #showEma;
    #showMacdhistdivergencescan;
    #tickCount;
    #parentContainer;
    #slideClassName;
    #tickers;
    constructor(row, col, height, width) {
        this.#row = row
        this.#col = col
        this.#height = height
        this.#width = width
        this.#tickers = []
        this.#currentSlideIndex = 0
        this.#slides = []
        this.#interval = "day"
        this.#tickCount = 1000
        this.#showEma = true
        this.#showMacdhistdivergencescan = true
        this.#parentContainer = document.getElementById(`gallery-container-${this.#row}-${this.#col}`);
        this.#slideClassName = "gallery-slide"
    }

    async show() {
        this.#initChartControls()
        
        // here sending a dummy ticker so that in server side we don't do repeated calls to
        // get ticker list
        var tickers = await this.#apiCall({ "query": `webserver --ticker all --do get --indicator tickers` });
        this.#tickers = tickers['tickers']
    
        this.#slides = Array(this.#tickers.length)
        this.#slides.fill(null)
        await this.#showSlide(this.#currentSlideIndex)
    }

    #initChartControls() {
        const prevBtn = document.getElementById(`prev-btn-${this.#row}-${this.#col}`);
        prevBtn.addEventListener('click', () => {
            if(this.#currentSlideIndex == 0) {
                this.#currentSlideIndex = this.#slides.length - 1
            }
            else {
                this.#currentSlideIndex -= 1
            }
            
            this.#showSlide(this.#currentSlideIndex);
        });

        const nextBtn = document.getElementById(`next-btn-${this.#row}-${this.#col}`);
        nextBtn.addEventListener('click', () => {
            if(this.#currentSlideIndex == this.#slides.length - 1) {
                this.#currentSlideIndex = 0
            }
            else {
                this.#currentSlideIndex += 1
            }
            
            this.#showSlide(this.#currentSlideIndex);
        });

        const selectedInterval = document.getElementById(`interval-${this.#row}-${this.#col}`)
        this.#interval = selectedInterval.value
        selectedInterval.addEventListener('change', async () => {
            this.#interval = selectedInterval.value
            this.#showSlide(this.#currentSlideIndex, true)
        })

        // const selectedIndicator = document.getElementById('indicator')
        // selectedIndicator.addEventListener('change', async () => {
        //     if (selectedIndicator.value == "EMA") {
        //         this.#showEma()
        //     }
        //     this.show()
        // })
    }

    #clearAllSlides() {
        var elements = document.getElementsByClassName(this.#slideClassName);
        elements = [...elements]
        elements = elements.filter(element => element.id == `${this.#slideClassName}-${this.#row}-${this.#col}`)
        elements.forEach(element => {
            element.parentNode.removeChild(element);
        });

        this.#slides = Array(this.#tickers.length)
        this.#slides.fill(null)
    }

    async #plotCandle(slideData) {
        var query_ohlc = { "query": `webserver --ticker ${slideData.symbol} --interval ${slideData.interval} --do get --indicator ohlc --n ${slideData.n}` }
        var resp_ohlc = await this.#apiCall(query_ohlc);
        resp_ohlc = this.#extractOhlc(resp_ohlc, slideData.symbol)
        const slide = document.createElement('div');
        slide.classList.add(`${this.#slideClassName}`);
        slide.setAttribute("id", `${this.#slideClassName}-${this.#row}-${this.#col}`)
        slide.innerHTML = `
              <h3>${slideData.symbol}</h3>
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

        //EMA
        if (slideData.ema) {
            var query_ema = { "query": `webserver --ticker ${slideData.symbol} --interval ${slideData.interval} --do get --indicator ema --n 1000` }
            var resp_ema = await this.#apiCall(query_ema);
            resp_ema = this.#extractIndicatorValue(resp_ema, slideData.symbol)
    
            const ema_series = tvChart.addLineSeries({ color: 'green', lineWidth: 1 });
            ema_series.setData(resp_ema);
        }

        //MACD Div
        if (slideData.macdhistdivergencescan) {
            var query_macd_div = { "query": `webserver --ticker ${slideData.symbol} --interval ${slideData.interval} --do get --indicator macdhistdivergencescan --n 100 --window 20` }
            var resp_macd_div = await this.#apiCall(query_macd_div);
            var signals_macd_div = this.#extractSignal(resp_macd_div, slideData.symbol)
            tvSeries.setMarkers(signals_macd_div);
        }

        return slide
    }

    async #showSlide(n, redraw=false) {
        if(redraw) {
            this.#clearAllSlides()
        }
        this.#slides.forEach(slide => {
            if(slide != null) {
                slide.style.display = 'none';
            }
        });

        if (this.#slides[n] == null) {
            var slideData = {
                symbol: this.#tickers[n], interval: this.#interval, n: this.#tickCount,
                'ema': this.#showEma, 'macdhistdivergencescan': this.#showMacdhistdivergencescan
            }
            var slide = await this.#plotCandle(slideData)
            this.#slides[n] = slide
        }
        
        this.#slides[n].style.display = 'block';
    }

    #convertToUtc(time) {
        var timestamp = time
        if (time.includes(":")) {
            timestamp = timestamp.replace(" ", "T")
            timestamp = timestamp + "+05:30"
            timestamp = new Date(timestamp)
            timestamp = timestamp.getTime()
            return timestamp
        }
        return timestamp
    }
    #extractOhlc(data, symbol) {
        var ohlc = []
        for (const [timestamp, map] of Object.entries(data[symbol])) {
            var row = {
                'time': this.#convertToUtc(timestamp),
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
                'time': this.#convertToUtc(time),
                'value': value
            }
            values.push(row)
        }
        return values
    }

    #extractSignal(data, symbol) {
        var signals = []
        for (const [time, value] of Object.entries(JSON.parse(data[symbol]))) {
            if (value === 1) {
                var row = {
                    'time': this.#convertToUtc(time),
                    'position': 'belowBar',
                    'color': 'green',
                    'shape': 'arrowUp',
                }
                signals.push(row)
            }
            else if (value === -1) {
                var row = {
                    'time': this.#convertToUtc(time),
                    'position': 'aboveBar',
                    'color': 'red',
                    'shape': 'arrowDown',
                }
                signals.push(row)
            }
        }
        return signals
    }

    async #apiCall(query) {
        var response = await fetch('http://localhost:8087/ohlc', {
            method: 'POST',
            body: JSON.stringify(query),
            headers: {
                'Content-Type': 'application/json'
            }
        }
        )
        var data = await response.json()

        return data
    }
}

async function renderChart(row, col, height, width) {
    chart = new TradingViewChart(row, col, height, width)
    chart.show()
};