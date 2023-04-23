class ColumnRight {
    #controls
    #row
    #col
    #parentId
    #scanners
    #indicators
    // multiple charts ie horizontal cols in a parent for multi-timeframe each 
    // col will contain multiple tvChart which will be displayed on the selected ticker
    #charts
    // #tvCharts 
    constructor(num, tickers, chartMap = {}) {
        this.#row = num;
        this.#col = 0;
        this.#controls = {}
        this.#controls["tickers"] = tickers;
        this.#controls["currentSlideIndex"] = 0
        this.#parentId = `column-${num}`;
        this.#scanners = {
            "macd_divergence": this.#addMacdDivergenceScanner
        }
        this.#indicators = {
            "ema": this.#addEmaIndicator,
            "volume": this.#addVolumeIndicator
        }
        this.#charts = chartMap
    }

    async init() {
        await this.#addCharts(this.#row, this.#col, this.#parentId)
        this.#initListeners();
    }
    async #addCharts(row, col, parentId) {
        var divId = `chart-container-${row}-${col}`
        this.#charts[divId] = {}
        this.#charts[divId]["scanners"] = {}
        this.#charts[divId]["indicators"] = {}
        // First add the controls to chart
        var options = {}
        // For next element /charts check if there already exists an element/chart
        // insert to the parent
        var innerHtml = `
        <select id="interval-${row}-${col}">
            <option value="hour">Hour</option>
            <option value="day" selected>Day</option>
            <option value="week">Week</option>
        </select>
        <select id="indicator-${row}-${col}">
            <option value="None" selected>None</option>
            <option value="ema">EMA</option>
            <option value="volume">Volume</option>
        </select>
        <select id="scanner-${row}-${col}">
            <option value="None">None</option>
            <option value="macd_divergence">MACD divergence</option>
        </select>`
        if (document.getElementById(`column-right-${this.#row}`) == null) {
            options["div"] = {
                "style": `display: flex`,
                "id": `column-right-${this.#row}`,
                "innerHTML": `
                <div id=${divId}>
                ${innerHtml}
                </div>
                `
            }
        } else {
            options["div"] = {
                "id": `${divId}`,
                "innerHTML": innerHtml
            }
        }

        options["events"] = {
            [`interval-${row}-${col}-change`]: {
                "target": `interval-${row}-${col}`,
                "type": "change",
                "callback": async (ev) => {
                    if (ev.target.id == `interval-${row}-${col}`) {
                        this.#controls["interval"] = ev.target.value
                        this.#charts[divId]["interval"] = ev.target.value
                        await this.#updateTvChart(ev.target.parentElement, this.#controls["ticker"], this.#controls["ticker"], col)
                    }
                }
            },
            [`scanner-${row}-${col}-click`]: {
                "target": `scanner-${row}-${col}`,
                "type": "click",
                "callback": (ev) => {
                    if (ev.target.id == `scanner-${row}-${col}` &&
                        ev.target.value != 'None') {
                        this.addScanner(row, col, ev)
                    }
                    document.getElementById(`scanner-${row}-${col}`).selectedIndex = 0
                }
            },
            [`indicator-${row}-${col}-input`]: {
                "target": `indicator-${row}-${col}`,
                "type": "input",
                "callback": (ev) => {
                    if (ev.target.id == `indicator-${row}-${col}` &&
                        ev.target.value != 'None') {
                        this.addIndicator(row, col, ev)
                    }
                    document.getElementById(`indicator-${row}-${col}`).selectedIndex = 0
                }
            }
        }

        addInnerHtmlToDiv(parentId, options);

        // Next add the tv chart
        var tvChart = new TradingViewChart(650, 1500)
        var divTvChart = await tvChart.plotCandle({
            symbol: this.#controls["tickers"][this.#controls["currentSlideIndex"]],
            interval: document.getElementById(`interval-${row}-${col}`).value,
            n: 1000,
            'indicators': this.#charts[divId]["indicators"],
            'scanners': this.#charts[divId]["scanners"]
        })
        document.getElementById(divId).appendChild(divTvChart)
        this.#charts[divId][divTvChart.id] = divTvChart
        this.#charts[divId]["tvChart"] = tvChart

        this.#resizeChartsInColumn()
    }

    #removeChart(row, col) {
        var chartId = `chart-container-${row}-${col}`
        var chart = document.getElementById(chartId)
        chart.remove()
        delete this.#charts[chartId]
        this.#resizeChartsInColumn()
    }

    async #showRow(previuosTicker, currentTicker) {
        var col = 0
        for (var chart in this.#charts) {
            var chartContainer = this.#charts[chart][previuosTicker].parentElement
            if (currentTicker in this.#charts[chart]) {
                chartContainer.removeChild(this.#charts[chart][previuosTicker])
                chartContainer.appendChild(this.#charts[chart][currentTicker])
            }
            else {
                await this.#updateTvChart(chartContainer, previuosTicker, currentTicker, col)
            }
            col += 1
        }
    }

    async #updateTvChart(chartContainer, tickerToRemove, currentTicker, col) {
        chartContainer.removeChild(this.#charts[chartContainer.id][tickerToRemove])
        var tvChart = new TradingViewChart(650, 1500)
        var divTvChart = await tvChart.plotCandle({
            symbol: currentTicker,
            interval: document.getElementById(`interval-${this.#row}-${col}`).value,
            n: 1000,
            'indicators': this.#charts[chartContainer.id]["indicators"],
            'scanners': this.#charts[chartContainer.id]["scanners"]
        })
        document.getElementById(chartContainer.id).appendChild(divTvChart)
        this.#charts[chartContainer.id][currentTicker] = divTvChart
        this.#charts[chartContainer.id]["tvChart"] = tvChart

        this.#resizeChartsInColumn()
    }

    #resizeChartsInColumn() {
        var avaialableWidth = window.innerWidth / Object.keys(this.#charts).length
        var avaialableHeight = window.innerHeight - 100
        var chartNum = 0
        for (var chart in this.#charts) {
            // There is only 1 tv-chart displayed
            var parent = document.getElementById(chart)
            parent.style.width = `${avaialableWidth}px`
            parent.style.height = `${avaialableHeight}px`
            this.#charts[chart]["tvChart"].setHeightWidth(avaialableHeight, avaialableWidth)

            var left = 30 + chartNum * avaialableWidth;
            // There can be multiple scanners
            var buttons = parent.getElementsByClassName("scanner-btn")
            for (var i = 0; i < buttons.length; i++) {
                buttons[i].style.left = `${left}px`;
            }

            // There can be multiple indicators
            buttons = parent.getElementsByClassName("indicator-btn")
            for (var i = 0; i < buttons.length; i++) {
                buttons[i].style.left = `${left}px`;
            }

            chartNum += 1
        }
    }

    setInterval(row, col, config={}) {
        var selectedInterval = document.getElementById(`interval-${row}-${col}`)
        var index = Array.from(selectedInterval.options).findIndex(option => option.value === config["interval"])
        selectedInterval.selectedIndex = index
        var event = new Event('change');
        selectedInterval.dispatchEvent(event);
    }

    addScanner(row, col, type, config = {}) {
        this.#scanners[type.target.value](row, col, config)
    }

    addIndicator(row, col, type, config = {}) {
        this.#indicators[type.target.value](row, col, config)
    }

    #initListeners() {
        const selectedTicker = document.getElementById(`ticker-select-${this.#row}`)
        this.#controls["currentSlideIndex"] = selectedTicker.selectedIndex
        this.#controls["ticker"] = selectedTicker.value
        selectedTicker.addEventListener('change', (event) => {
            this.#controls["currentSlideIndex"] = event.target.selectedIndex
            this.#showRow(this.#controls["ticker"], event.target.value)
            this.#controls["ticker"] = event.target.value
        })

        const addColumn = document.getElementById(`add-btn-${this.#row}`)
        addColumn.addEventListener('click', (event) => {
            this.insertNextChart(event)
        })

        const delColum = document.getElementById(`del-btn-${this.#row}`)
        delColum.addEventListener('click', (event) => {
            this.removeNextChart(event)
        })

        const saveConfig = document.getElementById(`save-btn-${this.#row}`)
        saveConfig.addEventListener('click', (event) => {
            apiPost("config", this.#charts)
        })
    }

    insertNextChart = async (ev) => {
        this.#col += 1
        await this.#addCharts(this.#row, this.#col, `column-right-${this.#row}`)
    }

    removeNextChart = (ev) => {
        if (this.#col > 0) {
            this.#removeChart(this.#row, this.#col)
            this.#col -= 1
        }
    }

    #addMacdDivergenceScanner = (row, col, config = {}) => {
        var updatechart = true
        var scannersMap = this.#charts[`chart-container-${row}-${col}`]["scanners"]
        var scannerId = `macd-divergence-scanner-${row}-${col}-#${Object.keys(scannersMap).length}`
        var top = 60 + (Object.keys(scannersMap).length + Object.keys(this.#charts[`chart-container-${row}-${col}`][`indicators`]).length) * 30;
        var left = 30 + col * screen.availWidth / Object.keys(this.#charts).length
        var options = {
            "div": {
                "style": `z-index: 99; position: absolute; top:${top}px; left:${left}px`,
                "class": "scanner-btn",
                "id": `div-${scannerId}`,
                "innerHTML": `
                <button id=button-${scannerId}>+</button>
                <div class=btn-popup id=popup-${scannerId} style="display: none; position: absolute; left:30px">
                    <form class=popup-form id=popup-form-${scannerId} >
                    <label for=rolling-window-${scannerId}>Rolling window</label>
                    <input type=number id=rolling-window-${scannerId} value=${config.window || 20} step=1><br>
                    <label for=full-window-${scannerId}>Full window</label>
                    <input type=number id=full-window-${scannerId} value=${config.n || 100} step=1><br>
                    <label for="buy-color-${scannerId}">Buy color</label>
                    <input id="buy-color-${scannerId}" type="color" value=${config.buyColor || "#00FF00"}>
                    <label for="sell-color-${scannerId}">Sell color</label>
                    <input id="sell-color-${scannerId}" type="color" value=${config.sellColor || "#FF0000"}>
                    </form>
                </div>
                `
            },
            "events": {
                [`button-${scannerId}-click`]: {
                    "target": `button-${scannerId}`,
                    "type": "click",
                    "callback": async (ev) => {
                        if (ev.target.id == `button-${scannerId}`) {
                            const popup = document.getElementById(`popup-${scannerId}`);
                            scannersMap[`div-${scannerId}`]["window"] = parseInt(document.getElementById(`rolling-window-${scannerId}`).value)
                            scannersMap[`div-${scannerId}`]["n"] = parseInt(document.getElementById(`full-window-${scannerId}`).value)
                            scannersMap[`div-${scannerId}`]["buyColor"] = document.getElementById(`buy-color-${scannerId}`).value
                            scannersMap[`div-${scannerId}`]["sellColor"] = document.getElementById(`sell-color-${scannerId}`).value
                            if (popup.style.display == 'block') {
                                popup.style.display = 'none'
                                if (updatechart) {
                                    await this.#updateTvChart(ev.target.parentElement.parentElement,
                                        this.#controls["ticker"], this.#controls["ticker"], col) // we update the chart removing the same ticker and updating
                                }
                            } else {
                                popup.style.display = 'block'
                            }
                        }
                    }
                },
                [`popup-form-${scannerId}-input`]: {
                    "target": `popup-form-${scannerId}`,
                    "type": "input",
                    "callback": (ev) => {
                        if (ev.currentTarget.id == `popup-form-${scannerId}`) {
                            updatechart = true
                        }
                    }
                },
                [`popup-form-${scannerId}-submit`]: {
                    "target": `popup-form-${scannerId}`,
                    "type": "submit",
                    "callback": (ev) => {
                        ev.preventDefault();
                    }
                }
            }
        }
        addInnerHtmlToDiv(`chart-container-${row}-${col}`, options)

        this.#charts[`chart-container-${row}-${col}`]["scanners"][`div-${scannerId}`] = {
            "window": parseInt(document.getElementById(`rolling-window-${scannerId}`).value),
            "n": parseInt(document.getElementById(`full-window-${scannerId}`).value),
            "type": "macd_divergence",
            "buyColor": document.getElementById(`buy-color-${scannerId}`).value,
            "sellColor": document.getElementById(`sell-color-${scannerId}`).value
        }
    }

    #addEmaIndicator = (row, col, config = {}) => {
        var updatechart = true
        var indicatorsMap = this.#charts[`chart-container-${row}-${col}`]["indicators"]
        var indicatorId = `ema-indicator-${row}-${col}-#${Object.keys(indicatorsMap).length}`
        
        // var id = `scanner-div-${scannerId}`
        var top = 60 + (Object.keys(this.#charts[`chart-container-${row}-${col}`][`scanners`]).length +
            Object.keys(indicatorsMap).length) * 30;
        var left = 30 + col * screen.availWidth / Object.keys(this.#charts).length
        var options = {
            "div": {
                "style": `z-index: 99; position: absolute; top:${top}px; left:${left}px`,
                "class": "indicator-btn",
                "id": `div-${indicatorId}`,
                "innerHTML": `
                <button id=button-${indicatorId}>+</button>
                <div class=btn-popup id=popup-${indicatorId} style="display: none; position: absolute; left:30px">
                    <form class=popup-form id=popup-form-${indicatorId} >
                    <label for=rolling-window-${indicatorId}>Rolling window</label>
                    <input type=number id=rolling-window-${indicatorId} value=${config.window || 20} step=1><br>
                    <label for="color-${indicatorId}">Color</label>
                    <input id="color-${indicatorId}" type="color" value=${config.color || "#00FF00"}><br>
                    </form>
                </div>
                `
            },
            "events": {
                [`button-${indicatorId}-click`]: {
                    "target": `button-${indicatorId}`,
                    "type": "click",
                    "callback": async (ev) => {
                        if (ev.target.id == `button-${indicatorId}`) {
                            const popup = document.getElementById(`popup-${indicatorId}`);
                            indicatorsMap[`div-${indicatorId}`]["window"] = parseInt(document.getElementById(`rolling-window-${indicatorId}`).value)
                            indicatorsMap[`div-${indicatorId}`]["color"] = document.getElementById(`color-${indicatorId}`).value
                            if (popup.style.display == 'block') {
                                popup.style.display = 'none'
                                if (updatechart) {
                                    await this.#updateTvChart(ev.target.parentElement.parentElement,
                                        this.#controls["ticker"], this.#controls["ticker"], col) // we update the chart removing the same ticker and updating
                                    updatechart = false
                                }
                            } else {
                                popup.style.display = 'block'
                            }
                        }
                    }
                },
                [`popup-form-${indicatorId}-input`]: {
                    "target": `popup-form-${indicatorId}`,
                    "type": "input",
                    "callback": (ev) => {
                        if (ev.currentTarget.id == `popup-form-${indicatorId}`) {
                            updatechart = true
                        }
                    }
                },
                [`popup-form-${indicatorId}-submit`]: {
                    "target": `popup-form-${indicatorId}`,
                    "type": "submit",
                    "callback": (ev) => {
                        ev.preventDefault();
                    }
                }
            }
        }
        addInnerHtmlToDiv(`chart-container-${row}-${col}`, options)

        this.#charts[`chart-container-${row}-${col}`]["indicators"][`div-${indicatorId}`] = {
            "window": parseInt(document.getElementById(`rolling-window-${indicatorId}`).value),
            "type": "ema",
            "color": document.getElementById(`color-${indicatorId}`).value
        }
    }

    #addVolumeIndicator = (row, col, config = {}) => {
        var updatechart = true
        var indicatorsMap = this.#charts[`chart-container-${row}-${col}`]["indicators"]
        var indicatorId = `volume-indicator${row}-${col}-#${Object.keys(indicatorsMap).length}`
        // var id = `scanner-div-${scannerId}`
        var top = 60 + (Object.keys(this.#charts[`chart-container-${row}-${col}`][`scanners`]).length +
            Object.keys(this.#charts[`chart-container-${row}-${col}`][`indicators`]).length) * 30;
        var left = 30 + col * screen.availWidth / Object.keys(this.#charts).length
        var options = {
            "div": {
                "style": `z-index: 99; position: absolute; top:${top}px; left:${left}px`,
                "class": "indicator-btn",
                "id": `div-${indicatorId}`,
                "innerHTML": `
                <button id=button-${indicatorId}>+</button>
                `
            }
        }
        addInnerHtmlToDiv(`chart-container-${row}-${col}`, options)

        this.#charts[`chart-container-${row}-${col}`]["indicators"][`div-${indicatorId}`] = {
            "type": "volume",
        }
    }
}

