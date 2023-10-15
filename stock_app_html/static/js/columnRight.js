class ColumnRight {
    #controls
    #row
    #col
    #parentId
    #indicators
    #height
    #width
    // multiple charts ie horizontal cols in a parent for multi-timeframe each 
    // col will contain multiple tvChart which will be displayed on the selected ticker
    #config
    // #tvCharts 
    constructor(num, tickers, height, width) {
        this.#row = num;
        this.#col = 0;
        this.#height = height
        this.#width = width
        this.#controls = {}
        this.#controls["tickers"] = tickers;
        this.#controls["currentSlideIndex"] = 0
        this.#parentId = `column-${num}`;
        this.#indicators = {
            "ema": this.#addEmaIndicator,
            "volume": this.#addVolumeIndicator
        }
        this.#config = {}
    }

    init = async (userConfig) => {
        var initListener = false
        for (var chart in userConfig) {
            var config = Object.assign({}, userConfig[chart])
            var col = parseInt(chart.split("-")[3])
            var row = parseInt(chart.split("-")[2])

            // Add first chart and initialise listeners
            if (!initListener) {
                await this.#addCharts(row, col, this.#parentId, config)
                this.#initListeners();
                initListener = true
                this.#col = col

            } else {
                // Insert next chart to column
                await this.#insertNextChart(false)
            }

            // Set Interval
            this.#setInterval(row, col, config)

            // Add indicators
            var indicators = config["indicators"]
            for (var indicator in indicators) {
                this.#addIndicator(row, col, { "target": { "value": indicators[indicator]["type"] } }, indicators[indicator])
            }
        }
    }

    getConfig() {
        return this.#config
    }

    // Add default chart
    async #addCharts(row, col, parentId, config = {}) {
        var divId = `chart-container-${row}-${col}`
        this.#config[divId] = {}
        this.#config[divId]["indicators"] = {}

        // First add the controls to chart
        var options = {}
        // For next element /charts check if there already exists an element/chart
        // insert to the parent
        var innerHtml = `
        <select id="interval-${row}-${col}">
            <option value="minute">Minute</option>    
            <option value="minute5">5 Minutes</option>
            <option value="minute15">15 Minutes</option>
            <option value="minute30">30 Minutes</option>
            <option value="hour">Hour</option>
            <option value="day" selected>Day</option>
            <option value="week">Week</option>
            <option value="month">Month</option>
        </select>
        <select id="indicator-${row}-${col}">
            <option value="None" selected>None</option>
            <option value="ema">EMA</option>
            <option value="volume">Volume</option>
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
                        this.#config[divId]["interval"] = ev.target.value
                        await this.#updateTvChart(ev.target.parentElement, this.#controls["ticker"], this.#controls["ticker"], col)
                    }
                }
            },
            [`indicator-${row}-${col}-input`]: {
                "target": `indicator-${row}-${col}`,
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
        var tvChart = new TradingViewChart(650, 1500)
        var divTvChart = await tvChart.plotCandle({
            symbol: this.#controls["tickers"][this.#controls["currentSlideIndex"]],
            interval: document.getElementById(`interval-${row}-${col}`).value,
            n: 1000,
            'indicators': {},
        })
        document.getElementById(divId).appendChild(divTvChart)
        this.#config[divId][divTvChart.id] = divTvChart
        this.#config[divId]["tvChart"] = tvChart
    }

    async #showRow(previuosTicker, currentTicker, meta=null) {
        var col = 0
        notifyLoad({ "state": "loading" })
        for (var chart in this.#config) {
            var chartContainer = this.#config[chart][previuosTicker].parentElement
            if (currentTicker in this.#config[chart]) {
                chartContainer.removeChild(this.#config[chart][previuosTicker])
                chartContainer.appendChild(this.#config[chart][currentTicker])
            }
            else {
                await this.#updateTvChart(chartContainer, previuosTicker, currentTicker, col, meta)
            }
            col += 1
        }

        notifyLoad({ "state": "loaded" })
    }

    async #updateTvChart(chartContainer, tickerToRemove, currentTicker, col, meta=null) {
        chartContainer.removeChild(this.#config[chartContainer.id][tickerToRemove])
        var tvChart = new TradingViewChart(650, 1500)
        var divTvChart = await tvChart.plotCandle({
            symbol: currentTicker,
            interval: document.getElementById(`interval-${this.#row}-${col}`).value,
            n: 1000, // TODO,
            meta: meta,
            'indicators': this.#config[chartContainer.id]["indicators"],
        })
        document.getElementById(chartContainer.id).appendChild(divTvChart)
        this.#config[chartContainer.id][currentTicker] = divTvChart
        this.#config[chartContainer.id]["tvChart"] = tvChart
        this.#resizeChartsInColumn()
    }

    #resizeChartsInColumn() {
        var avaialableWidth = this.#width / Object.keys(this.#config).length
        var avaialableHeight = this.#height - 100
        var chartNum = 0
        for (var chart in this.#config) {
            if (this.#config[chart]["tvChart"] != undefined) {
                // There is only 1 tv-chart displayed
                var parent = document.getElementById(chart)
                parent.style.position = "relative"
                parent.style.width = `${avaialableWidth}px`
                parent.style.height = `${avaialableHeight}px`
                this.#config[chart]["tvChart"].setHeightWidth(avaialableHeight, avaialableWidth)
                
                var left = 30;
                // There can be multiple indicators
                var buttons = parent.getElementsByClassName("indicator-btn")
                for (var i = 0; i < buttons.length; i++) {
                    buttons[i].style.left = `${left}px`;
                }

                chartNum += 1
            }
        }
    }

    #setInterval(row, col, config = {}) {
        var selectedInterval = document.getElementById(`interval-${row}-${col}`)
        var index = Array.from(selectedInterval.options).findIndex(option => option.value === config["interval"])
        selectedInterval.selectedIndex = index
        var event = new Event('change');
        selectedInterval.dispatchEvent(event);
    }

    #addIndicator(row, col, type, config = {}) {
        this.#indicators[type.target.value](row, col, config)
    }

    #initListeners() {
        const selectedTicker = document.getElementById(`ticker-select-${this.#row}`)
        this.#controls["currentSlideIndex"] = selectedTicker.selectedIndex
        this.#controls["ticker"] = selectedTicker.value
        selectedTicker.addEventListener('change', async (event) => {
            this.#controls["currentSlideIndex"] = event.target.selectedIndex
            await this.#showRow(this.#controls["ticker"], event.target.value, event.detail)
            this.#controls["ticker"] = event.target.value
        })

        const addColumn = document.getElementById(`add-btn-${this.#row}`)
        addColumn.addEventListener('click', async (event) => {
            await this.#insertNextChart(event)
        })

        const delColum = document.getElementById(`del-btn-${this.#row}`)
        delColum.addEventListener('click', (event) => {
            this.#removeNextChart(event)
        })
    }

    #insertNextChart = async (resizeChart = true) => {
        this.#col += 1
        await this.#addCharts(this.#row, this.#col, `column-right-${this.#row}`)
        if (resizeChart) {
            this.#resizeChartsInColumn()
        }
    }

    #removeNextChart = (resizeChart = true) => {
        if (this.#col > 0) {
            var chartId = `chart-container-${this.#row}-${this.#col}`
            var chart = document.getElementById(chartId)
            chart.remove()
            delete this.#config[chartId]
            this.#col -= 1
            if (resizeChart) {
                this.#resizeChartsInColumn()
            }
        }
    }

    #addEmaIndicator = (row, col, config = {}) => {
        var updatechart = false
        var indicatorsMap = this.#config[`chart-container-${row}-${col}`]["indicators"]
        var indicatorId = `ema-indicator-${row}-${col}-#${Object.keys(indicatorsMap).length}`

        // var id = `scanner-div-${scannerId}`
        var top = 30 + Object.keys(indicatorsMap).length * 30;
        var left = 30
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
        this.#config[`chart-container-${row}-${col}`]["indicators"][`div-${indicatorId}`] = {
            "window": parseInt(document.getElementById(`rolling-window-${indicatorId}`).value),
            "type": "ema",
            "color": document.getElementById(`color-${indicatorId}`).value
        }
    }

    #addVolumeIndicator = (row, col, config = {}) => {
        var updatechart = false
        var indicatorsMap = this.#config[`chart-container-${row}-${col}`]["indicators"]
        var indicatorId = `volume-indicator${row}-${col}-#${Object.keys(indicatorsMap).length}`
        // var id = `scanner-div-${scannerId}`
        var top = 30 + Object.keys(this.#config[`chart-container-${row}-${col}`][`indicators`]).length * 30;
        var left = 30
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

        this.#config[`chart-container-${row}-${col}`]["indicators"][`div-${indicatorId}`] = {
            "type": "volume",
        }
    }
}

