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
    constructor(num, tickers) {
        this.#row = num;
        this.#col = 0;
        this.#controls = {}
        this.#controls["tickers"] = tickers;
        this.#controls["currentSlideIndex"] = 0
        this.#parentId = `column-${num}`;
        this.#scanners = {}
        this.#indicators = {}
        this.#charts = {}
        this.#addCharts(this.#row, this.#col, this.#parentId)
        this.#initListeners();
    }

    #getControls(row, col) {
        this.#controls['tickcount'] = 1000
        this.#controls['interval'] = document.getElementById(`interval-${row}-${col}`).value
        this.#controls['scanners'] = this.#scanners
        this.#controls['indicators'] = this.#indicators

        return this.#controls
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
            <option value="None">None</option>
            <option value="ema">EMA</option>
            <option value="rsi" selected>RSI</option>
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
            [`interval-${row}-${col}`]: {
                "type": "change",
                "callback": (ev) => {
                    if (ev.target.id == `interval-${row}-${col}`) {           
                        this.#controls["interval"] = ev.target.value
                        this.#updateTvChart(ev.target.parentElement, this.#controls["ticker"], this.#controls["ticker"], col)
                    }
                }
            },
            [`scanner-${row}-${col}`]: {
                "type": "click",
                "callback": (ev) => {
                    if (ev.target.id == `scanner-${row}-${col}` &&
                        ev.target.value != 'None') {
                        this.#addScanner(row, col, ev)
                    }
                    document.getElementById(`scanner-${row}-${col}`).selectedIndex = 0
                }
            },
            [`indicator-${row}-${col}`]: {
                "type": "input",
                "callback": (ev) => {
                    if (ev.target.id == `indicator-${row}-${col}` &&
                        ev.target.value != 'None') {
                        this.#addIndicator(row, col, ev)
                    }
                    document.getElementById(`indicator-${row}-${col}`).selectedIndex = 0
                }
            }
        }

        addInnerHtmlToDiv(parentId, options);
        
        // Next add the tv chart
        var tvChart = await new TradingViewChart(650, 1500).plotCandle({
            symbol: this.#controls["tickers"][this.#controls["currentSlideIndex"]], 
            interval: document.getElementById(`interval-${row}-${col}`).value, 
            n: 1000,
            'indicators': this.#charts[divId]["indicators"], 
            'scanners': this.#charts[divId]["scanners"]
        })
        document.getElementById(divId).appendChild(tvChart)
        this.#charts[divId][tvChart.id] = tvChart
        this.#resizeChart()
        // Listen to which chart is selected
        // const selectedChart = document.getElementById(`${divId}`)
        // selectedChart.addEventListener("click", function() {
        //     this.classList.toggle("selected");
        // });
    }

    #removeElements(row, col) {
        var chart = document.getElementById(`chart-container-${row}-${col}`)
        chart.remove()
    }

    async #showRow(previuosTicker, currentTicker) {
        var col = 0
        for (var chart in this.#charts) {
            var chartContainer = this.#charts[chart][previuosTicker].parentElement
            if(currentTicker in this.#charts[chart]) {
                chartContainer.removeChild(this.#charts[chart][previuosTicker])
                chartContainer.appendChild(this.#charts[chart][currentTicker])
            }
            else {
                this.#updateTvChart(chartContainer, previuosTicker, currentTicker, col)
            }
            col += 1
        }
    }

    async #updateTvChart(chartContainer, tickerToRemove, currentTicker, col) {
        chartContainer.removeChild(this.#charts[chartContainer.id][tickerToRemove])
        var tvChart = await new TradingViewChart(650, 1500).plotCandle({
            symbol: currentTicker, 
            interval: document.getElementById(`interval-${this.#row}-${col}`).value, 
            n: 1000,
            'indicators': this.#charts[chartContainer.id]["indicators"], 
            'scanners': this.#charts[chartContainer.id]["scanners"]
        })

        document.getElementById(chartContainer.id).appendChild(tvChart)
        this.#charts[chartContainer.id][currentTicker] = tvChart
        this.#resizeChart()
    }

    #resizeChart() {
        var avaialableWidth = screen.availWidth / Object.keys(this.#charts).length
        var chartNum = 0
        for (var chart in this.#charts) {
            // There is only 1 tv-chart displayed
            var parent = document.getElementById(chart)
            parent.getElementsByClassName("tv-chart")[0].style.width = `${avaialableWidth}px`

            var left = 30 + chartNum*avaialableWidth;
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

    #addScanner(row, col, event) {
        switch (event.target.value) {
            case "macd_divergence":
                this.#addMacdDivergenceScanner(row, col)
                break
            default:
                console.log("Scanner not found")
        }
    }

    #addIndicator(row, col, event) {
        switch (event.target.value) {
            case "ema":
                this.#addEmaIndicator(row, col)
                break
            default:
                console.log("Indicator not found")
        }
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
            this.#col += 1
            this.#addCharts(this.#row, this.#col, `column-right-${this.#row}`)
        })

        const delColum = document.getElementById(`del-btn-${this.#row}`)
        delColum.addEventListener('click', (event) => {
            if (this.#col > 0) {
                this.#removeElements(this.#row, this.#col)
                this.#col -= 1
            }
        })
    }

    #addMacdDivergenceScanner(row, col) {
        var updatechart = true
        var scannerId = `${row}-${col}-${Date.now()}`
        var scannersMap = this.#charts[`chart-container-${row}-${col}`]["scanners"]
        // var id = `scanner-div-${scannerId}`
        var top = 60 + (Object.keys(this.#charts[`chart-container-${row}-${col}`][`scanners`]).length + 
        Object.keys(this.#charts[`chart-container-${row}-${col}`][`indicators`]).length) * 30;
        var left = 30 + col * screen.availWidth / Object.keys(this.#charts).length 
        var options = {
            "div": {
                "style": `z-index: 99; position: absolute; top:${top}px; left:${left}px`,
                "class": "scanner-btn",
                "id": `scanner-div-${scannerId}`,
                "innerHTML": `
                <button id=scanner-button-${scannerId}>+</button>
                <div class=btn-popup id=popup-${scannerId} style="display: none; position: absolute; left:30px">
                    <form class=popup-form id=popup-form-${scannerId} >
                    <label for=rolling-window-${scannerId}>Rolling window</label>
                    <input type=number id=rolling-window-${scannerId} value=20 step=1><br>
                    <label for=full-window-${scannerId}>Full window</label>
                    <input type=number id=full-window-${scannerId} value=100 step=1><br>
                    <label for="buy-color-${scannerId}">Buy color</label>
                    <input id="buy-color-${scannerId}" type="color" value="#00FF00">
                    <label for="sell-color-${scannerId}">Sell color</label>
                    <input id="sell-color-${scannerId}" type="color" value=#FF0000>
                    </form>
                </div>
                `
            },
            "events": {
                [`scanner-button-${scannerId}`]: {
                    "type": "click",
                    "callback": (ev) => {
                        if (ev.target.id == `scanner-button-${scannerId}`) {
                            const popup = document.getElementById(`popup-${scannerId}`);
                            if (popup.style.display == 'block') {
                                popup.style.display = 'none'
                                if (updatechart) {
                                    this.#updateTvChart(ev.target.parentElement.parentElement, 
                                        this.#controls["ticker"], this.#controls["ticker"], col) // we update the chart removing the same ticker and updating
                                }
                            } else {
                                popup.style.display = 'block'
                            }
                        }
                    }
                },
                [`popup-form-${scannerId}`]: {
                    "type": "input",
                    "callback": (ev) => {
                        if (ev.currentTarget.id == `popup-form-${scannerId}`) {
                            scannersMap[`scanner-div-${scannerId}`]["window"] = parseInt(document.getElementById(`rolling-window-${scannerId}`).value)
                            scannersMap[`scanner-div-${scannerId}`]["n"] = parseInt(document.getElementById(`full-window-${scannerId}`).value)
                            scannersMap[`scanner-div-${scannerId}`]["buyColor"] = document.getElementById(`buy-color-${scannerId}`).value
                            scannersMap[`scanner-div-${scannerId}`]["sellColor"] = document.getElementById(`sell-color-${scannerId}`).value

                            updatechart = true
                        }
                    }
                }
            }
        }
        addInnerHtmlToDiv(`chart-container-${row}-${col}`, options)

        scannersMap[`scanner-div-${scannerId}`] = {
            "window": parseInt(document.getElementById(`rolling-window-${scannerId}`).value),
            "n": parseInt(document.getElementById(`full-window-${scannerId}`).value),
            "type": "macd_divergence",
            "buyColor": document.getElementById(`buy-color-${scannerId}`).value,
            "sellColor": document.getElementById(`sell-color-${scannerId}`).value
        }
    }

    #addEmaIndicator(row, col) {
        var updatechart = true
        var indicatorId = `${row}-${col}-${Date.now()}`
        var indicatorsMap = this.#charts[`chart-container-${row}-${col}`]["indicators"]
        // var id = `scanner-div-${scannerId}`
        var top = 60 + (Object.keys(this.#charts[`chart-container-${row}-${col}`][`scanners`]).length + 
        Object.keys(this.#charts[`chart-container-${row}-${col}`][`indicators`]).length) * 30;
        var left = 30 + col * screen.availWidth / Object.keys(this.#charts).length
        var options = {
            "div": {
                "style": `z-index: 99; position: absolute; top:${top}px; left:${left}px`,
                "class": "indicator-btn",
                "id": `indicator-div-${indicatorId}`,
                "innerHTML": `
                <button id=indicator-button-${indicatorId}>+</button>
                <div class=btn-popup id=popup-${indicatorId} style="display: none; position: absolute; left:30px">
                    <form class=popup-form id=popup-form-${indicatorId} >
                    <label for=rolling-window-${indicatorId}>Rolling window</label>
                    <input type=number id=rolling-window-${indicatorId} value=20 step=1><br>
                    <label for="color-${indicatorId}">Color</label>
                    <input id="color-${indicatorId}" type="color" value="#00FF00"><br>
                    </form>
                </div>
                `
            },
            "events": {
                [`indicator-button-${indicatorId}`]: {
                    "type": "click",
                    "callback": (ev) => {
                        if (ev.target.id == `indicator-button-${indicatorId}`) {
                            const popup = document.getElementById(`popup-${indicatorId}`);
                            if (popup.style.display == 'block') {
                                popup.style.display = 'none'
                                if (updatechart) {
                                    this.#updateTvChart(ev.target.parentElement.parentElement, 
                                        this.#controls["ticker"], this.#controls["ticker"], col) // we update the chart removing the same ticker and updating
                                    updatechart = false
                                }
                            } else {
                                popup.style.display = 'block'
                            }
                        }
                    }
                },
                [`popup-form-${indicatorId}`]: {
                    "type": "input",
                    "callback": (ev) => {
                        if (ev.currentTarget.id == `popup-form-${indicatorId}`) {
                            indicatorsMap[`indicator-div-${indicatorId}`]["window"] = parseInt(document.getElementById(`rolling-window-${indicatorId}`).value)
                            indicatorsMap[`indicator-div-${indicatorId}`]["color"] = document.getElementById(`color-${indicatorId}`).value

                            updatechart = true
                        }
                    }
                }
            }
        }
        addInnerHtmlToDiv(`chart-container-${row}-${col}`, options)

        indicatorsMap[`indicator-div-${indicatorId}`] = {
            "window": parseInt(document.getElementById(`rolling-window-${indicatorId}`).value),
            "type": "ema",
            "color": document.getElementById(`color-${indicatorId}`).value
        }
    }
}

