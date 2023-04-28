class ColumnLeft {
    #controls
    #row
    #col
    #parentId
    #height
    #width
    // #tvCharts 
    constructor(num, tickers, height, width) {
        this.#row = num;
        this.#col = 0;
        this.#height = height
        this.#width = width
        this.#controls = {}
        this.#controls["tickers"] = tickers;
        this.#controls["currentSlideIndex"] = 0
        this.#parentId = `column-${num}`; // change
    }

    async init() {
        await this.#addMacdHistogramScannerDiv(this.#row, this.#col, this.#parentId)
        // this.#initListeners();
    }

    async #addMacdHistogramScannerDiv(row, col, parentId) {
        var divId = `macd-hist-scanner-${row}-${col}`
        var options = {
            "div": {
                "style": `width: ${this.#width}px;`,
                "id": `column-left-${this.#row}`,
                "innerHTML": `
                <div id=${divId}>
                <p style="margin-top: 0; margin-bottom: 0;">Macd Divergence</p>
                </div>
                `
            }
        }
        addInnerHtmlToDiv(parentId, options)

        // n > rolling window for macd calculations to happen
        var tickers = await apiPost("ohlc", {
            "query": `webserver --ticker all --do get \ 
        --indicator macddivergencelist --interval day --window 20 --n 21`});
        addListToDiv(divId, { 'list': tickers, 'id': `${divId}-list` })
    }

    #removeDiv(row, col) {
        // var chartId = `chart-container-${row}-${col}`
        // var chart = document.getElementById(chartId)
        // chart.remove()
        // delete this.#charts[chartId]
        // this.#resizeChartsInColumn()
    }
}

