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
        // Add a button to add queries
        this.#addQueryButton("gherkin-query-add", this.#row, this.#col, this.#parentId, userConfig)
    }

    getConfig() {
        return this.#config
    }

    #addQueryButton = (id, row, col, parentId, config = {}) => {
        var divId = `${id}-${row}-${col}`

        this.#config[divId] = {}
        this.#config[divId][id] = {}
        var queryCount = 0
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
                            var gherkinQueryId = `gherkin-query-${queryCount}`
                            var config = {} 
                            this.#addGherkinQueryDiv(gherkinQueryId, this.#row, this.#col, `column-left-${this.#row}`,
                            config)

                            queryCount += 1
                        }
                    }
                }
            }
        }
        addInnerHtmlToDiv(parentId, options)
        // this.#updateGherkinQueryList(id, divId, config)
    }

    #addGherkinQueryDiv = (id, row, col, parentId, config = {}) => {
        var divId = `${id}-${row}-${col}`

        this.#config[divId] = {}
        this.#config[divId][id] = {}
        var currentGherkin = ""
        var options = {
            "div": {
                "style": `width: ${this.#width}px;`,
                "id": `${divId}`,
                "innerHTML": `
                <p id=label-${divId} style="margin-top: 0; margin-bottom: 0;">Gherkin Query</p>
                <button id=button-query-${divId} style="margin-left: 10px">&#9881</button>
                <button id=button-dropdown-${divId} style="margin-left: 10px">&#x25BE</button>
                <button id=button-delete-${divId} style="margin-left: 10px">&#x2421</button>
                <div class=btn-popup id=popup-${divId} style="display: none; z-index: 999; background-color: darkgoldenrod; position: relative;">
                    <textarea id=input-${divId} type="text" placeholder="Enter your gherkin query here" 
                    style="position: absolute; top: 0; left: 100%; margin-left: 10px; height: 50vh; 
                    width: 30vw; overflow: scroll;"></textarea>
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
                                    await this.#updateGherkinQueryList(divId, this.#config[divId][id], query)
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
    }

    async #updateGherkinQueryList(divId, config, query) {
        var conjunction_keyword = ['And ', '* ']
        if (query != "" && query != undefined) {

            var gherkin_response = await apiPost(`gherkin-query`, {
                "query": `webserver --gherkin ${query} --indicator gherkin`
            });
            
            // User must define one feature per query
            var feature = Object.keys(gherkin_response["gherkin"])[0]
            document.getElementById(`label-${divId}`).innerText = feature
            var then_steps_tickers = []
            for (var scenario in gherkin_response['gherkin'][feature]) {
                var current_keyword = ""
                var steps = gherkin_response['gherkin'][feature][scenario]
                steps.forEach(step => {
                    if (step['type'] == 'Then ' || (current_keyword == 'Then ' && keyword in conjunction_keyword)) {
                        step['result']['tickers'].forEach(ticker => {
                            if (!then_steps_tickers.includes(ticker)) {
                                then_steps_tickers.push(
                                    {
                                        "text": ticker,
                                        "color": "black"
                                    }
                                )
                            }
                        })
                        current_keyword = 'Then '
                    }
                });
            }
            then_steps_tickers.sort(function (a, b) {
                if (a.text < b.text) {
                    return -1
                }
                if (a.text > b.text) {
                    return 1
                }
                return 0
            })

            var list = document.getElementById(`${divId}-list`)
            if (list != null) {
                list.remove()
            }

            addListToDiv(divId, then_steps_tickers, this.#clickToSelectTicker)
        }
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

