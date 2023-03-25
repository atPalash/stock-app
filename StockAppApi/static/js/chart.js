function convertToUtc(time) {
    var timestamp = time
    if(time.includes(":")) {
        timestamp = timestamp.replace(" ", "T")
        timestamp = timestamp + "+05:30"
        timestamp = new Date(timestamp)
        timestamp = timestamp.getTime()
        return timestamp
    }
    return timestamp
}
function extractOhlc(data, symbol) {
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

function extractIndicatorValue(data, symbol) {

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

function extractSignal(data, symbol) {
    var signals = []
    for (const [time, value] of Object.entries(JSON.parse(data[symbol]))) {
        if (value === 1) {
            var row = {
                'time': convertToUtc(time),
                'position': 'belowBar',
                'color': 'green',
                'shape': 'arrowUp',
            }
            signals.push(row)
        }
        else if (value === -1) {
            var row = {
                'time': convertToUtc(time),
                'position': 'aboveBar',
                'color': 'red',
                'shape': 'arrowDown',
            }
            signals.push(row)
        }
    }
    return signals
}

async function apiCall(query) {
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

async function plotChart(slidesData) {
    const galleryContainer = document.querySelector('.gallery-container');
    var elements = document.getElementsByClassName("gallery-slide");
    if(elements.length > 0) {
        while (elements.length > 0) {
            elements[0].parentNode.removeChild(elements[0]);
        }

        slides = []
    }
    
    slidesData.forEach(async (slideData, index) => {
        var query_ohlc = { "query": `webserver --ticker ${slideData.symbol} --interval ${slideData.interval} --do get --indicator ohlc --n ${slideData.n}` }
        var resp_ohlc = await apiCall(query_ohlc);
        resp_ohlc = extractOhlc(resp_ohlc, slideData.symbol)
        const slide = document.createElement('div');
        slide.classList.add('gallery-slide');
        slide.innerHTML = `
          <h3>${slideData.symbol}</h3>
          <div class="tv-chart-container">
            <div id="tv-chart-${index}" class="tv-chart"></div>
          </div>
        `;
        slide.style.display = 'none';
        galleryContainer.appendChild(slide);

        const tvChart = LightweightCharts.createChart(document.getElementById(`tv-chart-${index}`), {
            width: 1000,
            height: 400,
        });

        const tvSeries = tvChart.addCandlestickSeries();
        tvSeries.setData(resp_ohlc);

        //EMA
        if (slideData.ema) {
            var query_ema = { "query": `webserver --ticker ${slideData.symbol} --interval ${slideData.interval} --do get --indicator ema --n 1000` }
            var resp_ema = await apiCall(query_ema);
            resp_ema = extractIndicatorValue(resp_ema, slideData.symbol)
            const ema_series = tvChart.addLineSeries({ color: 'green', lineWidth: 1 });
            const ema_data = resp_ema;
            ema_series.setData(ema_data);
        }

        //MACD Div
        if (slideData.macdhistdivergencescan) {
            var query_macd_div = { "query": `webserver --ticker ${slideData.symbol} --interval ${slideData.interval} --do get --indicator macdhistdivergencescan --n 100 --window 20` }
            var resp_macd_div = await apiCall(query_macd_div);
            signals_macd_div = extractSignal(resp_macd_div, slideData.symbol)
            tvSeries.setMarkers(signals_macd_div);
        }

        slides.push(slide)
        showSlide(0)
    });
}

let currentSlide = 0;
let slides = [];

async function createChartControls() {
    const prevBtn = document.querySelector('.prev-btn');
    prevBtn.addEventListener('click', () => {
        showSlide(currentSlide - 1);
    });

    const nextBtn = document.querySelector('.next-btn');
    nextBtn.addEventListener('click', () => {
        showSlide(currentSlide + 1);
    });

    const selectedInterval = document.getElementById('interval')
    selectedInterval.addEventListener('change', async () => {
        await createChart(selectedInterval.value)
    })
    const selectedIndicator = document.getElementById('indicator').value

    await createChart(selectedInterval.value)
}
async function createChart(interval) {
    debugger
    showEma = true
    showMacdhistdivergencescan = true
    sampleCount = 1000
    var tickers = await apiCall({ "query": `webserver --ticker TCS --do get --indicator tickers` });
    slidesData = []
    tickers['TCS']['stock'].forEach(element => {
        slidesData.push({ symbol: element, interval: interval, n: sampleCount, 'ema': showEma, 'macdhistdivergencescan': showMacdhistdivergencescan })
    });

    await plotChart(slidesData);
}

function showSlide(n) {
    // const slides = document.querySelectorAll('.gallery-slide');
    if (n > slides.length - 1) {
        currentSlide = 0;
    } else if (n < 0) {
        currentSlide = slides.length - 1;
    } else {
        currentSlide = n;
    }
    slides.forEach(slide => {
        slide.style.display = 'none';
    });
    slides[currentSlide].style.display = 'block';
}

async function renderChart() {
    await createChartControls()
};