class ColumnLeft {
    #controls
    #row
    #col
    #parentId
    #height
    #width
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
        this.#parentId = `column-${num}`; // change
        this.#config = {}
    }

    init = async (userConfig) => {
        // // Add the 1st scanner to parent
        // var macdHistScannerId = "macd-hist-scanner"
        // this.#addMacdHistogramScannerDiv(macdHistScannerId, this.#row, this.#col, this.#parentId,
        //     userConfig[`${macdHistScannerId}-${this.#row}-${this.#col}`][macdHistScannerId])
        // Add the 1st scanner to parent
        var gherkinQueryId = "gherkin-query"
        this.#addGherkinQueryDiv(gherkinQueryId, this.#row, this.#col, this.#parentId,
            userConfig[`${gherkinQueryId}-${this.#row}-${this.#col}`][gherkinQueryId])

        // Add next ones to the existing div
        var stage2ScannerId = "stage2-scanner"
        this.#addStage2ScannerDiv(stage2ScannerId, this.#row, this.#col, `column-left-${this.#row}`,
            userConfig[`${stage2ScannerId}-${this.#row}-${this.#col}`][stage2ScannerId])
    }

    getConfig() {
        return this.#config
    }
    
    #addGherkinQueryDiv = (id, row, col, parentId, config = {}) => {
        var divId = `${id}-${row}-${col}`

        this.#config[divId] = {}
        this.#config[divId][id] = {}
        var currentGherkin = ""
        var options = {
            "div": {
                "style": `width: ${this.#width}px;`,
                "id": `column-left-${this.#row}`,
                "innerHTML": `
                <div id=${divId}>
                <div id=${divId}-controls style="display: flex;">
                <p style="margin-top: 0; margin-bottom: 0;">Gherkin Query</p>
                <button id=button-${divId} style="margin-left: 10px">&#9881</button>
                <div class=btn-popup id=popup-${divId} style="display: none; z-index: 999; background-color: darkgoldenrod; position: relative;">
                    <textarea id=input-${divId} type="text" placeholder="Enter your gherkin query here" 
                    style="position: absolute; top: 0; left: 100%; margin-left: 10px; height: 50vh; 
                    width: 30vw; overflow: scroll;"></textarea>
                </div>
                </div>
                </div>
                `
            },
            "events": {
                [`button-${divId}-click`]: {
                    "target": `button-${divId}`,
                    "type": "click",
                    "callback": async (ev) => {
                        if (ev.target.id == `button-${divId}`) {
                            const popup = document.getElementById(`popup-${divId}`);
                            const query = document.getElementById(`input-${divId}`).value
                            if (popup.style.display == 'block') {
                                popup.style.display = 'none'
                                if (query !== currentGherkin) {
                                    await this.#updateGherkinQueryList(id, divId, this.#config[divId][id], query)
                                    currentGherkin = query
                                }
                            } else {
                                popup.style.display = 'block'
                            }
                        }
                    }
                }
            }
        }
        addInnerHtmlToDiv(parentId, options)
        this.#updateGherkinQueryList(id, divId, config)
    }

    async #updateGherkinQueryList(id, divId, config, query) {
        if(query != "") {
            var tickers = await apiPost(`${id}`, {
                "query": `webserver --gherkin ${query} --indicator gherkin`
            });
        }
    }

    #addMacdHistogramScannerDiv = (id, row, col, parentId, config = {}) => {
        var updatechart = false
        var divId = `${id}-${row}-${col}`
        this.#config[divId] = {}
        this.#config[divId][id] = {}
        var options = {
            "div": {
                "style": `width: ${this.#width}px;`,
                "id": `column-left-${this.#row}`,
                "innerHTML": `
                <div id=${divId}>
                <div id=${divId}-controls style="display: flex;">
                <p style="margin-top: 0; margin-bottom: 0;">Macd Divergence</p>
                <button id=button-${divId} style="margin-left: 10px">&#9881</button>
                <div class=btn-popup id=popup-${divId} style="display: none; z-index: 99; background-color: darkgoldenrod; position: absolute; left:160px">
                    <form class=popup-form id=popup-form-${divId} >
                    <label for=interval-${divId}>Interval</label>
                    <select id="interval-${divId}">
                    <option value="hour">Hour</option>
                    <option value="day" selected>Day</option>
                    <option value="week">Week</option>
                    </select><br>
                    <label for=rolling-window-${divId}>Rolling window</label>
                    <input type=number id=rolling-window-${divId} value=${config.window || 20} step=1><br>
                    <label for=full-window-${divId}>Full window</label>
                    <input type=number id=full-window-${divId} value=${config.n || config.window + 1} step=1><br>
                    </form>
                </div>
                </div>
                </div>
                `
            },
            "events": {
                [`button-${divId}-click`]: {
                    "target": `button-${divId}`,
                    "type": "click",
                    "callback": async (ev) => {
                        if (ev.target.id == `button-${divId}`) {
                            const popup = document.getElementById(`popup-${divId}`);
                            if (popup.style.display == 'block') {
                                popup.style.display = 'none'
                                if (updatechart) {
                                    await this.#updateMacdDivergenceList(id, divId, this.#config[divId][id])
                                }
                            } else {
                                popup.style.display = 'block'
                            }
                        }
                    }
                },
                [`popup-form-${divId}-input`]: {
                    "target": `popup-form-${divId}`,
                    "type": "input",
                    "callback": (ev) => {
                        if (ev.currentTarget.id == `popup-form-${divId}`) {
                            updatechart = true
                            this.#config[divId][id]["window"] = parseInt(document.getElementById(`rolling-window-${divId}`).value)
                            this.#config[divId][id]["n"] = parseInt(document.getElementById(`full-window-${divId}`).value)
                            this.#config[divId][id]["interval"] = document.getElementById(`interval-${divId}`).value
                        }
                    }
                },
                [`popup-form-${divId}-submit`]: {
                    "target": `popup-form-${divId}`,
                    "type": "submit",
                    "callback": (ev) => {
                        ev.preventDefault();
                    }
                }
            }
        }
        addInnerHtmlToDiv(parentId, options)
        document.getElementById(`interval-${divId}`).value = config.interval
        this.#updateMacdDivergenceList(id, divId, config)
    }

    async #updateMacdDivergenceList(id, divId, config) {
        var tickers = await apiPost(`${id}`, {
            "query": `webserver --ticker all --do get \ 
        --indicator macddivergencelist --interval ${config.interval} --window ${config.window} \
        --n ${config.n}`
        });

        var macdHistTickers = []
        for (var ticker in tickers) {
            var signal = tickers[ticker]
            if (signal == 1) {
                macdHistTickers.push({
                    "text": ticker,
                    "color": "green"
                })
            } else if (signal == -1) {
                macdHistTickers.push({
                    "text": ticker,
                    "color": "red"
                })
            }
        }

        var list = document.getElementById(`${divId}-list`)
        if (list != null) {
            list.remove()
        }

        addListToDiv(divId, macdHistTickers, this.#clickToSelectTicker)
    }

    #addStage2ScannerDiv = (id, row, col, parentId, config = {}) => {
        var updatechart = false
        var divId = `${id}-${row}-${col}`

        this.#config[divId] = {}
        this.#config[divId][id] = {}
        var options = {
            "div": {
                "style": `width: ${this.#width}px;`,
                "id": `column-left-${this.#row}`,
                "innerHTML": `
                <div id=${divId}>
                <div id=${divId}-controls style="display: flex;">
                <p style="margin-top: 0; margin-bottom: 0;">Stage2</p>
                <button id=button-${divId} style="margin-left: 10px">&#9881</button>
                <div class=btn-popup id=popup-${divId} style="display: none; z-index: 99; background-color: darkgoldenrod; position: absolute; left:160px">
                    <form class=popup-form id=popup-form-${divId} >
                    <label for=type-${divId}>Type</label>
                    <select id="type-${divId}">
                    <option value="ma" selected>Ma</option>
                    <option value="ema">Ema</option>
                    </select><br>
                    <label for=interval-${divId}>Interval</label>
                    <select id="interval-${divId}">
                    <option value="hour">Hour</option>
                    <option value="day" selected>Day</option>
                    <option value="week">Week</option>
                    </select><br>
                    <label for=full-window-${divId}>Full window</label>
                    <input type=number id=full-window-${divId} value=${config.n || 30} step=1><br>
                    </form>
                </div>
                </div>
                </div>
                `
            },
            "events": {
                [`button-${divId}-click`]: {
                    "target": `button-${divId}`,
                    "type": "click",
                    "callback": async (ev) => {
                        if (ev.target.id == `button-${divId}`) {
                            const popup = document.getElementById(`popup-${divId}`);
                            if (popup.style.display == 'block') {
                                popup.style.display = 'none'
                                if (updatechart) {
                                    await this.#updateStage2ScannerList(id, divId, this.#config[divId][id])
                                }
                            } else {
                                popup.style.display = 'block'
                            }
                        }
                    }
                },
                [`popup-form-${divId}-input`]: {
                    "target": `popup-form-${divId}`,
                    "type": "input",
                    "callback": (ev) => {
                        if (ev.currentTarget.id == `popup-form-${divId}`) {
                            updatechart = true
                            this.#config[divId][id]["type"] = document.getElementById(`type-${divId}`).value
                            this.#config[divId][id]["interval"] = document.getElementById(`interval-${divId}`).value
                            this.#config[divId][id]["n"] = parseInt(document.getElementById(`full-window-${divId}`).value)
                        }
                    }
                },
                [`popup-form-${divId}-submit`]: {
                    "target": `popup-form-${divId}`,
                    "type": "submit",
                    "callback": (ev) => {
                        ev.preventDefault();
                    }
                }
            }
        }
        addInnerHtmlToDiv(parentId, options)
        document.getElementById(`interval-${divId}`).value = config.interval
        this.#updateStage2ScannerList(id, divId, config)
    }

    async #updateStage2ScannerList(id, divId, config) {
        var tickers = await apiPost(`${id}`, {
            "query": `webserver --ticker all --do get --indicator stage2scanner 
            --interval ${config.interval} --n ${config.n} --stage2scannertype ${config.type}`
        });

        var stage2tickers = []
        for (var k in tickers) {
            var temp = JSON.parse(tickers[k])
            if (temp.valid) {
                stage2tickers.push({
                    "text": temp.stock,
                    "color": "black"
                })
            }
        }

        var list = document.getElementById(`${divId}-list`)
        if (list != null) {
            list.remove()
        }

        addListToDiv(divId, stage2tickers, this.#clickToSelectTicker)
    }

    #clickToSelectTicker = (evt) => {
        var id = `ticker-select-0`
        var index = Array.from(document.getElementById(id).children).findIndex(function (ele) {
            if (ele.innerText == evt.target.innerText) {
                return true;
            }
        })
        if (index == -1) {
            console.error("Should not happen")
            return
        }
        changeSelection(id, index)
    }
}

