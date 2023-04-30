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
        this.#addMacdHistogramScannerDiv(this.#row, this.#col, this.#parentId, 
            userConfig[`macd-hist-scanner-${this.#row}-${this.#col}`]["macd-hist-scanner"])
    }

    getConfig() {
        return this.#config
    }
    
    #addMacdHistogramScannerDiv = (row, col, parentId, config = {}) => {
        var updatechart = false
        var divId = `macd-hist-scanner-${row}-${col}`
        this.#config[divId] = {}
        this.#config[divId]["macd-hist-scanner"] = {}
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
                                    await this.#updateMacdDivergenceList(divId, this.#config[divId]["macd-hist-scanner"])
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
                            this.#config[divId]["macd-hist-scanner"]["window"] = parseInt(document.getElementById(`rolling-window-${divId}`).value)
                            this.#config[divId]["macd-hist-scanner"]["n"] = parseInt(document.getElementById(`full-window-${divId}`).value)
                            this.#config[divId]["macd-hist-scanner"]["interval"] = document.getElementById(`interval-${divId}`).value
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
        this.#updateMacdDivergenceList(divId, config)
    }

    async #updateMacdDivergenceList(divId, config) {
        var tickers = await apiPost("ohlc", {
            "query": `webserver --ticker all --do get \ 
        --indicator macddivergencelist --interval ${config.interval} --window ${config.window} \
        --n ${config.n}`
        });
    
        var list = document.getElementById(`${divId}-list`) 
        if( list!= null) {
            list.remove()
        }
        addListToDiv(divId, { 'list': tickers, 'id': `${divId}-list` })
    }
}

