class ColumnLeft {
    #controls
    #row
    #parentId
    #allTickersOtherStockData
    #otherStockData
    constructor(num, tickers) {
        this.#row = num;
        this.#controls = {}
        this.#controls["tickers"] = tickers;
        this.#controls["currentSlideIndex"] = 0
        this.#parentId = `column-${num}`;
        this.#allTickersOtherStockData = {}
        this.#otherStockData = {
            "Elder impulse": this.#elderImpulse,
            // "Canslim": this.#canslim
        }
        this.#addElements()
    }

    async #addElements() {
        // var style = `background-color: #f2f2f2;
        // display: inline-block;
        // float:left;`
        var options = {
            "div": {
                // "style": style,
                "class": "column-left",
                "id": `column-left-${this.#row}`
            }
        }

        addInnerHtmlToDiv(`${this.#parentId}`, options);

        this.#initListeners();
        this.#showOtherStockData(this.#controls["tickers"][this.#controls["currentSlideIndex"]])
    }

    #initListeners() {
        const selectedTicker = document.getElementById(`ticker-select-${this.#row}`)
        selectedTicker.addEventListener('change', (event) => {
            this.#controls["currentSlideIndex"] = event.target.selectedIndex
            this.#showOtherStockData(this.#controls["tickers"][this.#controls["currentSlideIndex"]])
        })
    }

    async #elderImpulse(ticker) {
        // if(ticker in this.#allTickersOtherStockData) {
        //     return this.#allTickersOtherStockData[ticker]
        // }
        var query = { "query": `webserver --ticker ${ticker} \
        --do get --indicator elderimpulse --n 100 --window 13 --n 100 \
        --macd_fast_period 13 --macd_slow_period 26 --macd_signal_period 9` }
        var resp = await apiCall(query);
        resp = JSON.parse(resp[ticker])["trend"]
        // this.#allTickersOtherStockData[ticker] = {"Elder impulse" : resp}
        return resp
    }

    async #canslim(ticker) {
        debugger
        var query = { "query": `webserver --ticker ${ticker} \
        --do get --indicator canslim --n 400 --window 13 --n 100 ` }
        var resp = await apiCall(query);
        resp = resp[ticker]
        // this.#allTickersOtherStockData[ticker] = {"Elder impulse" : resp}
        return resp
    }

    async #showOtherStockData(ticker) {
        // var parentDiv = document.getElementById(`column-left-${this.#row}`)
        // parentDiv.innerHTML = ""
            
        // for(var key in this.#otherStockData) {
        //     var data = await this.#otherStockData[key](ticker)   
        // }
        // parentDiv.appendChild(text)
        console.log("hello");
    }
}

