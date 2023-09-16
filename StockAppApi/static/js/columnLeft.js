class ColumnLeft {
    #controls
    #row
    #col
    #parentId
    #height
    #width
    #config
    #queryCount
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
        this.#queryCount = 0
    }

    init = async (userConfig) => {
        // Add a button to add queries
        this.#addQueryButton("gherkin-query-add", this.#row, this.#col, this.#parentId)

        // Add the queries from user config
        for (let key in userConfig) {
            var gherkinQueryId = `gherkin-query-${this.#queryCount}`
            this.#addGherkinQueryDiv(gherkinQueryId, this.#row, this.#col, `column-left-${this.#row}`, userConfig[key])
            this.#queryCount += 1

        }
    }

    getConfig() {
        var queries = document.getElementsByClassName(`input-query`)
        for (let i = 0; i < queries.length; i++) {
            this.#config[queries[i].id] = queries[i].value
        }
        return this.#config
    }

    #addQueryButton = (id, row, col, parentId) => {
        var divId = `${id}-${row}-${col}`

        var options = {
            "div": {
                "style": `width: ${this.#width}px;`,
                "id": `column-left-${this.#row}`,
                "innerHTML": `
                <div id=${divId}>
                <button id=button-${divId} style="margin-left: 10px">Add query</button>
                </div>
                `
            },
            "events": {
                [`button-${divId}-click`]: {
                    "target": `button-${divId}`,
                    "type": "click",
                    "callback": async (ev) => {
                        if (ev.target.id == `button-${divId}`) {
                            var gherkinQueryId = `gherkin-query-${this.#queryCount}`
                            this.#addGherkinQueryDiv(gherkinQueryId, this.#row, this.#col, `column-left-${this.#row}`,
                                "")
                            this.#queryCount += 1
                        }
                    }
                }
            }
        }
        addInnerHtmlToDiv(parentId, options)
        // this.#updateGherkinQueryList(id, divId, config)
    }

    #addGherkinQueryDiv = (id, row, col, parentId, textQuery) => {
        var divId = `${id}-${row}-${col}`
        var currentGherkin = ""
        var options = {
            "div": {
                "style": `width: ${this.#width}px;`,
                "class": "text-query",
                "id": `${divId}`,
                "innerHTML": `
                <p id=label-${divId} style="margin-top: 0; margin-bottom: 0;">Gherkin Query</p>
                <button id=button-query-${divId} style="margin-left: 10px">&#9881</button>
                <button id=button-dropdown-${divId} style="margin-left: 10px">&#x25BE</button>
                <button id=button-delete-${divId} style="margin-left: 10px">&#x2421</button>
                <div class=btn-popup id=popup-${divId} style="display: none; z-index: 999; background-color: darkgoldenrod; position: relative;">
                    <textarea id=input-${divId} class="input-query" type="text" placeholder="Enter your gherkin query here" 
                    style="position: absolute; top: 0; left: 100%; margin-left: 10px; height: 50vh; 
                    width: 30vw; overflow: scroll;">${textQuery}</textarea>
                </div>
                <div class=chart-popup id=chart-popup-${divId} style="display: none; z-index: 999; background-color: darkgoldenrod; position: relative;">
                </div>
                `
            },
            "events": {
                [`button-query-${divId}-click`]: {
                    "target": `button-query-${divId}`,
                    "type": "click",
                    "callback": async (ev) => {
                        if (ev.target.id == `button-query-${divId}`) {
                            const popup = document.getElementById(`popup-${divId}`);
                            const query = document.getElementById(`input-${divId}`).value
                            if (popup.style.display == 'block') {
                                popup.style.display = 'none'
                                if (query !== currentGherkin) {
                                    await this.#updateGherkinQueryList(divId, query)
                                    currentGherkin = query
                                }
                            } else {
                                popup.style.display = 'block'
                            }
                        }
                    }
                },
                [`button-dropdown-${divId}`]: {
                    "target": `button-dropdown-${divId}`,
                    "type": "click",
                    "callback": (ev) => {
                        if (ev.currentTarget.id == `button-dropdown-${divId}`) {
                            var list = document.getElementById(`${divId}-list`);
                            if (list != null) {
                                if (list.style.display === "none") {
                                    list.style.display = "block";
                                    ev.currentTarget.innerText = getUnicodeIcon("&#x25B4");
                                } else {
                                    list.style.display = "none";
                                    ev.currentTarget.innerText = getUnicodeIcon("&#x25BE");
                                }
                            }
                        }
                    }
                },
                [`button-delete-${divId}`]: {
                    "target": `button-delete-${divId}`,
                    "type": "click",
                    "callback": (ev) => {
                        if (ev.currentTarget.id == `button-delete-${divId}`) {
                            var div = document.getElementById(`${divId}`);
                            div.remove()
                        }
                    }
                }
            }
        }
        addInnerHtmlToDiv(parentId, options)
        // execute query when loaded with prexisting config query. 2 times to open and close
        document.getElementById(`button-query-${divId}`).click()
        document.getElementById(`button-query-${divId}`).click()
    }

    async #updateGherkinQueryList(divId, query) {
        var conjunction_keyword = ['And ', '* ']
        if (query != "" && query != undefined) {
            try {
                var gherkin_response = await apiPost(`gherkin-query`, {
                    "query": `webserver --gherkin ${query} --indicator gherkin`
                });
                
                // User must define one feature per query
                var feature = Object.keys(gherkin_response["gherkin"])[0]
                document.getElementById(`label-${divId}`).innerText = feature
                var then_steps_tickers = []
                var ticker_signals = {}
                for (var scenario in gherkin_response['gherkin'][feature]) {
                    var current_keyword = ""
                    var steps = gherkin_response['gherkin'][feature][scenario]
                    steps.forEach(step => {
                        if (step['type'] == 'Then ' || (current_keyword == 'Then ' && keyword in conjunction_keyword)) {
                            step['result']['tickers'].forEach(ticker => {
                                var ticker_sigs = step['result']['signals'][ticker]
                                if (ticker in ticker_signals) {
                                    ticker_signals[ticker]["signals"].push(...ticker_sigs)
                                } else {
                                    ticker_signals[ticker] = { "signals": ticker_sigs }
                                }
                            })
                            current_keyword = 'Then '
                        }
                    });
                }

                var list = document.getElementById(`${divId}-list`)
                if (list != null) {
                    list.remove()
                }

                addListToDiv(divId, ticker_signals, this.#clickToSelectTicker)
            } catch (error) {
                console.error('An error occurred during gherkin query', error);
            }
        }
    }

    #clickToSelectTicker = async (evt) => {
        // id of top-nav ticker selector
        var id = `ticker-select-0`
        var tickerSelector = document.getElementById(id)
        var index = Array.from(tickerSelector.children).findIndex(function (ele) {
            if (ele.innerText == evt.target.innerText) {
                return true;
            }
        })
        if (index == -1) {
            console.error("Should not happen")
            return
        }

        var popupId = `chart-popup-gherkin-query-0-0-0`
        var meta = evt.target.getAttribute('meta-data') != null ? JSON.parse(evt.target.getAttribute('meta-data')) : null
        if (meta['signals'] != null && meta['signals'].length > 0) {
            var popup = document.getElementById(popupId)
            popup.innerHTML = ""
            // var existingTvCharts = popup.getElementsByClassName("tv-chart");
            // while (existingTvCharts.length > 0) {
            //     existingTvCharts[0].parentNode.removeChild(existingTvCharts[0]);
            // }

            var tvChart = new TradingViewChart(500, 1000)
            var divTvChart = await tvChart.plotCandle({
                symbol: evt.target.innerText,
                interval: meta['signals'][0]['interval'],
                n: 1000, // TODO,
                meta: meta,
                style: "position: absolute; top: 0; left: 100%; margin-left: 10px;"
            })
            popup.appendChild(divTvChart)

            if(tickerSelector.value == evt.target.innerText) {
                if (popup.style.display == 'block') {
                    popup.style.display = 'none'
                } else {
                    popup.style.display = 'block'
                }
            }
            else {
                popup.style.display = 'block'
            }
        }

        // changeSelection(id, index, evt.target.getAttribute('meta-data'))
        changeSelection(id, index)
    }
}

