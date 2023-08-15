class TopNavigation {
    #controls
    #row
    #parentId

    constructor(num, tickers) {
        this.#row = num;
        this.#controls = {}
        this.#controls["tickers"] = tickers;
        this.#controls["currentSlideIndex"] = 0;
        this.#parentId = `row-container-${num}`;

        this.#addElements()
        this.#initListeners()
    }

    #addElements() {
        var options = {
            "div": {
                "style": `border: 1px solid red`,
                "class": "ticker-navigation-container",
                "id": `ticker-navigation-container-${this.#row}`,
                "innerHTML": `
                <button class="btn" id="prev-btn-${this.#row}">&lt;</button>
                <button class="btn" id="next-btn-${this.#row}">&gt;</button>
                <select id="ticker-select-${this.#row}"></select>
                <button class="btn" id="add-btn-${this.#row}">+</button>
                <button class="btn" id="del-btn-${this.#row}">x</button>
                <button class="btn" id="save-btn-${this.#row}">&#x1F4BE</button>
                `
            },
            "events": {
                [`prev-btn-${this.#row}-click`]: {
                    "target": `prev-btn-${this.#row}`,
                    "type": "click",
                    "callback": (ev) => {
                        if (ev.target.id == `prev-btn-${this.#row}`) {
                            if (this.#controls["currentSlideIndex"] == 0) {
                                this.#controls["currentSlideIndex"] = this.#controls["tickers"].length - 1
                            }
                            else {
                                this.#controls["currentSlideIndex"] -= 1
                            }
                        }
                        changeSelection(`ticker-select-${this.#row}`, this.#controls["currentSlideIndex"])
                    }
                },
                [`next-btn-${this.#row}-click`]: {
                    "target": `next-btn-${this.#row}`,
                    "type": "click",
                    "callback": (ev) => {
                        if (ev.target.id == `next-btn-${this.#row}`) {
                            if (this.#controls["currentSlideIndex"] == this.#controls["tickers"].length - 1) {
                                this.#controls["currentSlideIndex"] = 0
                            }
                            else {
                                this.#controls["currentSlideIndex"] += + 1
                            }
                            changeSelection(`ticker-select-${this.#row}`, this.#controls["currentSlideIndex"])
                        }
                    }
                },
                [`ticker-select-${this.#row}-input`]: {
                    "target": `ticker-select-${this.#row}`,
                    "type": "input",
                    "callback": (ev) => {
                        if (ev.target.id == `ticker-select-${this.#row}`) {
                            this.#controls["currentSlideIndex"] = ev.target.selectedIndex
                        }
                    }
                }
            }
        }

        addInnerHtmlToDiv(`${this.#parentId}`, options);
        
        // Populate the ticker-select
        const selectedTicker = document.getElementById(`ticker-select-${this.#row}`)
        for(var ticker of this.#controls["tickers"]) {
            selectedTicker.add(new Option(ticker, ticker))
        }
    }

    #initListeners() {
        document.addEventListener('load', (event) => {
            switch(event.detail.state) {
                case "loading":
                    toggleDivChild(`ticker-navigation-container-${this.#row}`, false)
                    break
                case "loaded":
                    toggleDivChild(`ticker-navigation-container-${this.#row}`, true)
                    break
                default:
                    console.log("Should not happen")
            }
        });
    }
}

