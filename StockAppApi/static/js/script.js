class Row {
    #controls
    #row
    #parentId

    constructor(num) {
        this.#row = num;
        this.#controls = {}
        this.#parentId = `row`;

        this.#addElements()
    }

    #addElements() {
        var options = {
            "div": {
                "style": `display: grid; grid-auto-rows: minmax(10px, auto);`,
                "class": "row-container",
                "id": `row-container-${this.#row}`
            }
        }
        addInnerHtmlToDiv(`${this.#parentId}`, options);
    }

    setChild(id, childElement) {
        this.#controls[id] = childElement
    }
}

async function render() {
    var tickers = await apiPost("ohlc",{ "query": `webserver --ticker all --do get --indicator tickers` });
    tickers = tickers["tickers"]
    var row = new Row(0)

    var topNavigation = new TopNavigation(0, tickers)
    var container = new Container(0, tickers)

    row.setChild("topNavigation", topNavigation)
    row.setChild("container", container)
}

render()
