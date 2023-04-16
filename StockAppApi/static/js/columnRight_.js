class ColumnRight {
    #height
    #width
    #columnRight
    #scanners
    #indicators
    #controls
    #row
    constructor(num, tickers) {
        this.#columnRight = document.getElementById(`column-right-${num}`);
        this.#height = this.#columnRight.offsetHeight
        this.#width = this.#columnRight.offsetWidth
        this.#controls = {}
        this.#scanners = {}
        this.#indicators = {}
        this.#controls["tickers"] = tickers
        this.#row = num
    }

    async #initControls(row, col) {
        this.#controls["currentSlideIndex"] = 0

        const topNavAddChartBtn = document.getElementById(`top-nav-add-chart-btn-${row}-${col}`)
        topNavAddChartBtn.addEventListener('click', () => {
            var arr = topNavAddChartBtn.id.split("-")
            var rowToAdd = parseInt(arr[arr.length - 2])
            var colToAdd = parseInt(arr[arr.length - 1]) + 1
            this.addChart(false, rowToAdd, colToAdd)
        });

        const topNavRemoveChartBtn = document.getElementById(`top-nav-remove-chart-btn-${row}-${col}`)
        topNavRemoveChartBtn.addEventListener('click', () => {
            this.removeChart(row, col)
        });

        const bottomNavAddChartBtn = document.getElementById(`bottom-nav-add-chart-btn-${row}-${col}`)
        bottomNavAddChartBtn.addEventListener('click', () => {
            var arr = bottomNavAddChartBtn.id.split("-")
            var rowToAdd = parseInt(arr[arr.length - 2]) + 1
            var colToAdd = 0
            this.addChart(true, rowToAdd, colToAdd)
        });

        const bottomNavRemoveChartBtn = document.getElementById(`bottom-nav-remove-chart-btn-${row}-${col}`)
        bottomNavRemoveChartBtn.addEventListener('click', () => {
            this.removeChart(row, col)
        });
        
        const selectedTicker = document.getElementById(`ticker-select-${this.#row}`)
        selectedTicker.addEventListener('change', (event) => {
            this.#controls["currentSlideIndex"] = event.target.selectedIndex
            showChart(this.#controls, false)
        })
       
        const interval = document.getElementById(`interval-${row}-${col}`)
        interval.addEventListener('change', (event) => {
            this.#controls["interval"] = event.target.value
            showChart(this.#controls, true)
        });

        const addScanner = document.getElementById(`scanner-${row}-${col}`)
        addScanner.addEventListener('click', (event) => {
            if (event.target.value != "None") {
                this.#addScanner(row, col, event)
                showChart(this.#controls, true)
            }
            addScanner.selectedIndex = 0
        });

        const addIndicator = document.getElementById(`indicator-${row}-${col}`)
        addIndicator.addEventListener('click', (event) => {
            if (event.target.value != "None") {
                this.#addIndicator(row, col, event)
                showChart(this.#controls, true)
            }
            addIndicator.selectedIndex = 0
        });
    }

    #addInnerHtmlToDiv(parentId, options) {
        var parent = document.getElementById(parentId)
        var childDiv = document.createElement("div")

        for (var key in options["div"]) {
            var val = options["div"][key]
            switch (key) {
                case "id":
                    childDiv.id = val
                    break
                case "style":
                    childDiv.style = val
                    break
                case "class":
                    childDiv.classList.add(val)
                    break
                case "innerHTML":
                    childDiv.innerHTML = val
                    break
            }
        }
        parent.appendChild(childDiv)

        for (var evnt in options["events"]) {
            var listenerElement = document.getElementById(evnt)
            var val = options["events"][evnt]
            listenerElement.addEventListener(val["type"], val["callback"]);
        }
    }

    removeChart(row, col) {
        var chart = document.getElementById(`chart-tv-with-controls-${row}-${col}`)
        chart.remove()
    }

    #getControls(row, col) {
        this.#controls['tickcount'] = 1000
        this.#controls['interval'] = document.getElementById(`interval-${row}-${col}`).value
        this.#controls['scanners'] = this.#scanners
        this.#controls['indicators'] = this.#indicators

        return this.#controls
    }

    #addMacdDivergenceScanner(row, col) {
        var updatechart = true
        var scannerId = `${row}-${col}-${Date.now()}`
        // var id = `scanner-div-${scannerId}`
        var top = 30 + (Object.keys(this.#scanners).length + Object.keys(this.#indicators).length) * 30;
        var style = `position: absolute; z-index: 99; top:${top}px; left:0px`
        var options = {
            "div": {
                "style": style,
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
                                    showChart(this.#controls, true)
                                    // renderChart(row, col, 500, 1200, this.#getControls(row, col), true)
                                    // var parent = document.getElementById(`gallery-container-${row}-${col}`)
                                    // var thisChild = document.getElementById(`scanner-div-${scannerId}`)
                                    // parent.appendChild(thisChild)

                                    updatechart = false
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
                            this.#scanners[`scanner-div-${scannerId}`]["window"] = parseInt(document.getElementById(`rolling-window-${scannerId}`).value)
                            this.#scanners[`scanner-div-${scannerId}`]["n"] = parseInt(document.getElementById(`full-window-${scannerId}`).value)
                            this.#scanners[`scanner-div-${scannerId}`]["buyColor"] = document.getElementById(`buy-color-${scannerId}`).value
                            this.#scanners[`scanner-div-${scannerId}`]["sellColor"] = document.getElementById(`sell-color-${scannerId}`).value

                            updatechart = true
                        }
                    }
                }
            }
        }
        this.#addInnerHtmlToDiv(`gallery-container-${row}-${col}`, options)

        this.#scanners[`scanner-div-${scannerId}`] = {
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
        // var id = `scanner-div-${scannerId}`
        var top = 30 + (Object.keys(this.#scanners).length + Object.keys(this.#indicators).length) * 30;
        var style = `position: absolute; z-index: 99; top:${top}px; left:0px`
        var options = {
            "div": {
                "style": style,
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
                                    showChart(this.#controls, true)
                                    // renderChart(row, col, 500, 1200, this.#getControls(row, col), true)
                                    // var parent = document.getElementById(`gallery-container-${row}-${col}`)
                                    // var thisChild = document.getElementById(`indicator-div-${indicatorId}`)
                                    // parent.appendChild(thisChild)

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
                            this.#indicators[`indicator-div-${indicatorId}`]["window"] = parseInt(document.getElementById(`rolling-window-${indicatorId}`).value)
                            this.#indicators[`indicator-div-${indicatorId}`]["color"] = document.getElementById(`color-${indicatorId}`).value

                            updatechart = true
                        }
                    }
                }
            }
        }
        this.#addInnerHtmlToDiv(`gallery-container-${row}-${col}`, options)

        this.#indicators[`indicator-div-${indicatorId}`] = {
            "window": parseInt(document.getElementById(`rolling-window-${indicatorId}`).value),
            "type": "ema",
            "color": document.getElementById(`color-${indicatorId}`).value
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

    async addChart(asRow = true, row, col) {
        var rowDiv = null
        if (asRow) {
            rowDiv = document.createElement("div")
            rowDiv.classList.add("chart-row")
            rowDiv.setAttribute("id", `chart-row-${row}`)
        }

        var chartDiv = document.createElement("div")
        if (!asRow) {
            rowDiv = document.getElementById(`chart-row-${row}`)
            // chartDiv.style.display = "flex";
            // chartDiv.style.flexDirection = "column";
        }
        chartDiv.classList.add("chart-tv-with-controls")
        chartDiv.setAttribute("id", `chart-tv-with-controls-${row}-${col}`)

        chartDiv.innerHTML = `
        <div class="navigation" id="top-nav-${row}-${col}">
        <button id="top-nav-add-chart-btn-${row}-${col}">+</button>
        <button id="top-nav-remove-chart-btn-${row}-${col}">X</button>
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
        </select>
        <div class="arrow-container" id="arrow-container-${row}-${col}">
        </div>
        <div class="gallery-container" id="gallery-container-${row}-${col}">
        </div>
        <div class="navigation" id="bottom-nav-${row}-${col}">
            <button id="bottom-nav-add-chart-btn-${row}-${col}">+</button>
            <button id="bottom-nav-remove-chart-btn-${row}-${col}">X</button>
        </div>
        `;
        if (asRow) {
            rowDiv.appendChild(chartDiv);
            this.#columnRight.appendChild(rowDiv);
        } else {
            rowDiv.appendChild(chartDiv);
        }

        await this.#initControls(row, col)
        renderChart(row, col, 500, 1200, this.#getControls(row, col));
    }
}
