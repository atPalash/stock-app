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

        this.#loadUserConfig()
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

    async #loadUserConfig() {
        var config = await apiGet("config")
        config = JSON.parse(config)
        for (var chart in config) {
            var col = parseInt(chart.split("-")[3])
            var row = parseInt(chart.split("-")[2])
            if (col == 0) {
                this.columnRight = new ColumnRight(row, this.#controls["tickers"])
                await this.columnRight.init()
            } else {
                await this.columnRight.insertNextChart({})
            }
        }

        this.#loadMeta(config)
    }

    #loadMeta(config) {
        for (var chart in config) {
            var col = parseInt(chart.split("-")[3])
            var row = parseInt(chart.split("-")[2])

            this.columnRight.setInterval(row, col, config[`chart-container-${row}-${col}`])
            var indicators = config[chart]["indicators"]
            for (var indicator in indicators) {
                this.columnRight.addIndicator(row, col, {"target": { "value": indicators[indicator]["type"] }}, indicators[indicator])
            }

            var scanners = config[chart]["scanners"]
            for (var scanner in scanners) {
                this.columnRight.addScanner(row, col, {"target": { "value": scanners[scanner]["type"] }}, scanners[scanner])
            }
        }
    }
}

