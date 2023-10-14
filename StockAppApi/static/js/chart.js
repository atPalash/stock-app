class TradingViewChart {
    #height
    #width
    #chart
    #slide
    #tooltip
    constructor(height, width) {
        this.#height = height
        this.#width = width
        this.#chart = null
        this.#slide = null
        this.#tooltip = {'signals':{}, 'width': 100}
    }

    setHeightWidth(height, width) {
        this.#slide.style.width = `${width}px`
        this.#slide.style.height = `${height}px`
        this.#chart.applyOptions({ height: height, width: width });
    }
    async plotCandle(slideData) {
        var query_ohlc = { "query": `webserver --ticker ${slideData.symbol} --interval ${slideData.interval} --do get --indicator ohlc --n ${slideData.n}` }
        var data_ohlc = await apiPost("ohlc", query_ohlc);
        var resp_ohlc = this.#extractOhlc(data_ohlc, slideData.symbol)
        const slide = document.createElement('div');
        slide.classList.add(`tv-chart`);
        slide.setAttribute("id", `${slideData.symbol}`)
        if (slideData.style == null) {
            slide.style.display = 'block';
        } else {
            slide.style = slideData.style
        }

        const intervalsWithOutTime = ["month", "week", "day"]
        const tvChart = LightweightCharts.createChart(slide, {
            // autoSize: true
            height: this.#height,
            width: this.#width,
            timeScale: {
                timeVisible: !intervalsWithOutTime.includes(slideData.interval),
                timeFormat: '%h:%m',
            },
        });

        tvChart.applyOptions({
            rightPriceScale: {
                visible: true,
            },
            crosshair: {
                horzLine: {
                    visible: true,
                    labelVisible: true,
                },
                vertLine: {
                    visible: true,
                    style: 0,
                    width: 2,
                    color: 'rgba(32, 38, 46, 0.1)',
                    labelVisible: true,
                },
            },
            // hide the grid lines
            grid: {
                vertLines: {
                    visible: false,
                },
                horzLines: {
                    visible: false,
                },
            },
        });

        const tvSeries = tvChart.addCandlestickSeries();
        tvSeries.priceScale().applyOptions({
            scaleMargins: {
                top: 0.3, // leave some space for the legend
                bottom: 0.25,
            },
        });
        tvSeries.setData(resp_ohlc);

        // Create and style the tooltip html element
        const toolTip = document.createElement('div');
        toolTip.style = `width: ${this.#tooltip['width']}px; height: 300px; position: absolute; display: none; padding: 8px; box-sizing: border-box; font-size: 12px; text-align: left; z-index: 1000; top: 12px; left: 12px; pointer-events: none; border-radius: 4px 4px 0px 0px; border-bottom: none; box-shadow: 0 2px 5px 0 rgba(117, 134, 150, 0.45);font-family: -apple-system, BlinkMacSystemFont, 'Trebuchet MS', Roboto, Ubuntu, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;`;
        toolTip.style.background = `rgba(${'255, 255, 255'}, 0.25)`;
        toolTip.style.color = 'black';
        toolTip.style.borderColor = 'rgba( 239, 83, 80, 1)';
        slide.appendChild(toolTip);

        // update tooltip
        tvChart.subscribeCrosshairMove(param => {
            if (
                param.point === undefined ||
                !param.time ||
                param.point.x < 0 ||
                param.point.x > slide.clientWidth ||
                param.point.y < 0 ||
                param.point.y > slide.clientHeight
            ) {
                toolTip.style.display = 'none';
            } else {
                // time will be in the same format that we supplied to setData.
                // thus it will be YYYY-MM-DD
                const dateStr = param.time;
                toolTip.style.display = 'block';
                const data = param.seriesData.get(tvSeries);
                const price = data.value !== undefined ? data.value : data.close;
                
                var tooltipData = this.#tooltip
                toolTip.innerHTML = `
                <div style="color: ${'rgba( 239, 83, 80, 1)'}">⬤ ${slideData.symbol}
                </div>
                `;
                if(tooltipData['signals'].hasOwnProperty(dateStr)) {
                    tooltipData['signals'][dateStr].forEach(element => {
                        toolTip.innerHTML += `
                        <div style="color: ${'rgba( 239, 83, 80, 1)'}">${element}
                        </div>
                        `
                    });
                }
                

                let left = param.point.x; // relative to timeScale
                const timeScaleWidth = tvChart.timeScale().width();
                const priceScaleWidth = tvChart.priceScale('left').width();
                const halfTooltipWidth = this.#tooltip['width'] / 2;
                left += priceScaleWidth - halfTooltipWidth;
                left = Math.min(left, priceScaleWidth + timeScaleWidth - this.#tooltip['width']);
                left = Math.max(left, priceScaleWidth);

                toolTip.style.left = left + 'px';
                toolTip.style.top = 0 + 'px';
            }
        });

        // tvChart.timeScale().fitContent();

        // go through each desired indicator and plot them
        for (let key in slideData.indicators) {
            var indicator = slideData.indicators[key]
            switch (indicator['type']) {
                case 'ema':
                    var query = {
                        "query": `webserver --ticker ${slideData.symbol} \
                    --interval ${slideData.interval} --do get --indicator ema \
                    --window ${indicator["window"]} --n ${slideData.n}`
                    }
                    var resp = await apiPost("ohlc", query);
                    var series = this.#extractIndicatorValue(resp, slideData.symbol)
                    const chartSeries = tvChart.addLineSeries({ color: indicator['color'], lineWidth: 1 });
                    chartSeries.setData(series);
                    break;
                case 'volume':
                    var series = resp_ohlc.map(item => {
                        return { time: item.time, value: item.volume, color: item.open > item.close ? 'red' : 'green' };
                    });
                    const volumeSeries = tvChart.addHistogramSeries({
                        color: '#26a69a',
                        priceFormat: {
                            type: 'volume',
                        },
                        priceScaleId: ''
                    });
                    volumeSeries.priceScale().applyOptions({
                        // set the positioning of the volume series
                        scaleMargins: {
                            top: 0.8, // highest point of the series will be 70% away from the top
                            bottom: 0,
                        },
                    });
                    volumeSeries.setData(series)
                    break
                default:
                    console.log("Indicator not avaialable")
            }
        }

        // go throught each desired scanner and plot signals
        if (slideData.meta != null) {
            var meta_dict = slideData.meta
            var signal_offset = 0
            for (let key in meta_dict) {
                switch (key) {
                    case 'signals':
                        meta_dict[key].forEach(element => {
                            var ret = this.#extractSignal(element['color'], element['signal'], element['step'].split('|')[1].trim())
                            const tempSeries = tvChart.addLineSeries({
                                color: 'rgba(255, 255, 255, 0)', // hide or show the line by setting opacity
                                lastValueVisible: false, // hide value from y axis
                                priceLineVisible: false
                            });
                            const tempCloseSeries = []
                            resp_ohlc.forEach(element => {
                                tempCloseSeries.push({
                                    'time': element['time'],
                                    'value': element['low'] + signal_offset
                                })
                            })
                            tempSeries.setData(tempCloseSeries);
                            tempSeries.setMarkers(ret)
                            signal_offset -= 10
                        });
                        break;
                    default:
                        console.log("Scanner not avaialable")
                }
            }
        }

        this.#chart = tvChart
        this.#slide = slide
        return slide
    }

    #extractOhlc(data, symbol) {
        var ohlc = []
        for (const [timestamp, map] of Object.entries(data[symbol])) {
            var row = {
                'time': convertToUtc(timestamp),
                'open': map['Open'],
                'high': map['High'],
                'low': map['Low'],
                'close': map['Close'],
                'volume': map['Volume']
            }
            ohlc.push(row)
        }
        return ohlc
    }

    #extractIndicatorValue(data, symbol) {
        var values = []
        for (const [time, value] of Object.entries(JSON.parse(data[symbol]))) {
            var row = {
                'time': convertToUtc(time),
                'value': value
            }
            values.push(row)
        }
        return values
    }

    #extractSignal(color, signals, step) {
        var ret = []
        signals.forEach(element => {
            var time = convertToUtc(element[1])
            if (element[2]) {
                var row = {
                    'time': time,
                    'position': element[3] < 0 ? 'aboveBar' : 'belowBar',
                    'color': element[3] < 0 ? 'red' : color,
                    'shape': element[3] < 0 ? 'arrowDown' : 'arrowUp',
                }
                ret.push(row)
            }
            
            if(this.#tooltip['signals'].hasOwnProperty(time)) {
                this.#tooltip['signals'][time].push(step)
            } else {
                this.#tooltip['signals'][time] = [step]
            }
        })
        return ret
    }
}
