class Container {
    #controls
    #row
    #parentId
    #config
    constructor(num, tickers) {
        this.#row = num;
        this.#controls = {}
        this.#controls["tickers"] = tickers;

        this.#parentId = `row-container-${num}`;

        this.#initListeners()
        this.#addElements()
        this.#loadUserConfig()
        this.#config = {}
    }

    #addElements() {
        var options = {
            "div": {
                "style": `border: 1px solid red; display:flex; justify-content: space-between; `,
                "class": "column",
                "id": `column-${this.#row}`
            }
        }

        addInnerHtmlToDiv(`${this.#parentId}`, options);
    }

    async #loadUserConfig() {
        debugger
        var configData = JSON.parse(localStorage.getItem('userConfig'));
        if (configData) {
            this.#config = configData
        } else {
            var res = await apiGet("config")
            this.#config = JSON.parse(res)
        }
        notifyLoad({ 'state': "loading" })

        this.columnLeft = new ColumnLeft(0, this.#controls["tickers"], screen.availHeight * 0.95, screen.availWidth * 0.1)
        this.columnLeft.init(this.#config['column-left'])

        this.columnRight = new ColumnRight(0, this.#controls["tickers"], screen.availHeight * 0.95, screen.availWidth * 0.9)
        await this.columnRight.init(this.#config['column-right'])

        notifyLoad({ 'state': "loaded" })
    }

    #initListeners() {
        const saveConfig = document.getElementById(`save-btn-${this.#row}`)
        saveConfig.addEventListener('click', async (event) => {
            debugger
            this.#config["column-left"] = this.columnLeft.getConfig()
            this.#config["column-right"] = this.columnRight.getConfig()

            var configData = { 'column-left': this.#config["column-left"], 'column-right': this.#config["column-right"] }
            localStorage.setItem('userConfig', JSON.stringify(configData));
            // await apiPost("config", configData)
        })
    }
}

