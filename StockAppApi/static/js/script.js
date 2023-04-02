class PageRight {
    #height
    #width
    #columnRight
    constructor() {
        this.#columnRight = document.getElementById("column-right");
        this.#height = this.#columnRight.offsetHeight
        this.#width = this.#columnRight.offsetWidth
    }

    #initControls(row, col) {
        const topNavAddChartBtn = document.getElementById(`top-nav-add-chart-btn-${row}-${col}`)
        topNavAddChartBtn.addEventListener('click', () => {
            var arr = topNavAddChartBtn.id.split("-")
            var rowToAdd = parseInt(arr[arr.length-2])
            var colToAdd = parseInt(arr[arr.length-1]) + 1
            this.addChart(false, rowToAdd, colToAdd)
        });

        const topNavRemoveChartBtn = document.getElementById(`top-nav-remove-chart-btn-${row}-${col}`)
        topNavRemoveChartBtn.addEventListener('click', () => {
            this.removeChart(row, col)
        });

        const bottomNavAddChartBtn = document.getElementById(`bottom-nav-add-chart-btn-${row}-${col}`)
        bottomNavAddChartBtn.addEventListener('click', () => {
            debugger
            var arr = bottomNavAddChartBtn.id.split("-")
            var rowToAdd = parseInt(arr[arr.length-2]) + 1
            var colToAdd = 0
            this.addChart(true, rowToAdd, colToAdd)
        });

        const bottomNavRemoveChartBtn = document.getElementById(`bottom-nav-remove-chart-btn-${row}-${col}`)
        bottomNavRemoveChartBtn.addEventListener('click', () => {
            this.removeChart(row,col)
        });
    }

    removeChart(row, col) {
        var chart = document.getElementById(`chart-tv-with-controls-${row}-${col}`)
        chart.remove()
    }

    addChart(asRow=true, row, col) { 
        var rowDiv = null  
        if(asRow) {
            rowDiv = document.createElement("div")
            rowDiv.classList.add("chart-row")
            rowDiv.setAttribute("id", `chart-row-${row}`)
        }
        
        var chartDiv = document.createElement("div")    
        if(!asRow) {
            rowDiv = document.getElementById(`chart-row-${row}`)
            // chartDiv.style.display = "flex";
            // chartDiv.style.flexDirection = "column";
        }
        chartDiv.classList.add("chart-tv-with-controls")
        chartDiv.setAttribute("id", `chart-tv-with-controls-${row}-${col}`)
        
        chartDiv.innerHTML = `
        <div class="navigation" id="top-nav-${row}-${col}">
        <button id="top-nav-add-chart-btn-${row}-${col}">+</button>
        <button id="top-nav-remove-chart-btn-${row}-${col}">X</button>
        <select id="interval-${row}-${col}">
          <option value="hour">Hour</option>
          <option value="day" selected>Day</option>
          <option value="week">Week</option>
        </select>
        <select id="indicator-${row}-${col}">
          <option value="ema">EMA</option>
          <option value="rsi" selected>RSI</option>
        </select>
        <select id="scanner-${row}-${col}">
          <option value="ema">EMA</option>
          <option value="rsi" selected>RSI</option>
        </select>
        <div class="arrow-container" id="arrow-container-${row}-${col}">
        <button class="prev-btn" id="prev-btn-${row}-${col}">&#10094;</button>
        <button class="next-btn" id="next-btn-${row}-${col}">&#10095;</button>
        </div>
        </div>
        <div class="gallery-container" id="gallery-container-${row}-${col}">
        </div>
        <div class="navigation" id="bottom-nav-${row}-${col}">
            <button id="bottom-nav-add-chart-btn-${row}-${col}">+</button>
            <button id="bottom-nav-remove-chart-btn-${row}-${col}">X</button>
        </div>
        `;
        if (asRow) {
            rowDiv.appendChild(chartDiv);
            this.#columnRight.appendChild(rowDiv);
        } else {
            rowDiv.appendChild(chartDiv);
        }
        
        this.#initControls(row, col)
        renderChart(row, col, 500, 1200);
    }
}

function render() {
    var pageRight = new PageRight()
    pageRight.addChart(true, 0, 0)
}

render()
