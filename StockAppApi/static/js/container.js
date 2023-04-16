class Container {
    #controls
    #row
    #parentId

    constructor(num, tickers) {
        this.#row = num;
        this.#controls = {}
        this.#controls["tickers"] = tickers;
        
        this.#parentId = `row-container-${num}`;

        this.#addElements()

        this.columnLeft = new ColumnLeft(num, tickers)
        this.columnRight = new ColumnRight(num, tickers)
        // this.columnRight.addChart(true, num, 0)
    }

    #addElements() {
        var options = {
            "div": {
                "style": `border: 1px solid red`,
                "class": "column",
                "id": `column-${this.#row}`
            }
        }

        addInnerHtmlToDiv(`${this.#parentId}`, options);
    }
}

