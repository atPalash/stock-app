async function apiPost(endPoint, query) {
    var response = await fetch(`https://communal-vocal-mayfly.ngrok-free.app/${endPoint}`, {
        method: 'POST',
        body: JSON.stringify(query),
        headers: {
            'Content-Type': 'application/json'
        }
    }
    )
    var data = await response.json()

    return data
}

async function apiGet(endPoint) {
    var response = await fetch(`https://communal-vocal-mayfly.ngrok-free.app/${endPoint}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    }
    )
    var data = await response.json()

    return data
}

function convertToUtc(time) {
    if (time.includes(":")) {
        // This offset will change based on the source data and client
        // time zone, also when DST is applied. Also strip the timezone 
        // part kindoff a hacky way since the yfinance data in hour has
        // time zone but the 30m ,15m charts have no time zone. Here, we remove
        // the timezone part if any.
        const offset = 10800 + 9000
        return Date.parse(time.substring(0, 19)) / 1000 + offset
    }
    return time
}

function addInnerHtmlToDiv(parentId, options) {
    var parent = document.getElementById(parentId)
    var childDiv = document.createElement("div")

    for (var key in options["div"]) {
        var val = options["div"][key]
        switch (key) {
            case "id":
                childDiv.id = val
                break
            case "style":
                childDiv.style = val
                break
            case "class":
                childDiv.classList.add(val)
                break
            case "innerHTML":
                childDiv.innerHTML = val
                break
        }
    }
    parent.appendChild(childDiv)

    for (var evnt in options["events"]) {
        var val = options["events"][evnt]
        var listenerElement = document.getElementById(val["target"])
        listenerElement.addEventListener(val["type"], val["callback"]);
    }
}

function addListToDiv(parentId, ticker_list, clickHandler = null, contextHandler = null, context_menu_query_id = "") {
    // Create the unordered list element
    const ul = document.createElement('ul');
    ul.setAttribute('id', `${parentId}-list`)
    ul.setAttribute('style', "margin-top: 0; margin-bottom: 0;")

    ticker_list.forEach(ticker => {
        const li = document.createElement('li');
        li.textContent = ticker;
        li.style.color = "black"
        if (contextHandler != null) {
            li.addEventListener("contextmenu", (event) => {
                event.preventDefault();
                hideContextMenus();

                const rect = li.getBoundingClientRect();
                const top = rect.top;
                const left = rect.left + rect.width * 0.5;
                contextHandler(event, top, left, li, context_menu_query_id)
            })
        }
        ul.appendChild(li);
    })

    // Append the unordered list to the body of the page
    document.getElementById(parentId).appendChild(ul);
    ul.addEventListener('mouseover', function (event) {
        if (event.target.matches('li')) {
            event.target.style.cursor = 'pointer';
        }
    });

    if (clickHandler != null) {
        ul.addEventListener("click", (event) => {
            clickHandler(event)
        })
    }
}

function hideContextMenus() {
    Array.from(document.getElementsByClassName('context-menu')).forEach(menu => {
        menu.style.display = 'none';
    });
}

function notifyLoad(data = {}) {
    const loadEvent = new CustomEvent('load', { detail: data });
    document.dispatchEvent(loadEvent);
}

function toggleDivChild(divId, enabled) {
    const myDiv = document.getElementById(divId);
    const children = myDiv.querySelectorAll('*');

    children.forEach(child => {
        if (child.tagName === 'INPUT' || child.tagName === 'TEXTAREA' || child.tagName === 'SELECT' || child.tagName === 'BUTTON') {
            child.disabled = !enabled;
        }
    });
}

function parseJSON(jsonString) {
    var thisJson = {}
    try {
        var jObj = JSON.parse(jsonString)
        for (var key in jObj) {
            thisJson[key] = parseJSON(jObj[key])
        };
    } catch (error) {
        for (var key in jsonString) {
            thisJson[key] = parseJSON(jObj[key])
        };
    }
    return thisJson;
}

function changeSelection(id, index, detail = null) {
    var select = document.getElementById(id)
    select.selectedIndex = index
    var event = new Event('change');
    event.detail = detail
    select.dispatchEvent(event);
}

function popUpSelection(id, index, detail = null) {
    var select = document.getElementById(id)
    select.selectedIndex = index
    var event = new Event('change');
    event.detail = detail
    select.dispatchEvent(event);
}


function getUnicodeIcon(uniStr) {
    var decimalValue = parseInt(uniStr.substr(3), 16);
    return String.fromCharCode(decimalValue);
}

function openWindow(parentId, elementToUpdate) {
    var parent = document.getElementById(parentId)
    parent.innerHTML = `<button id="${parentId}-closeButton" style="position: absolute; top: 10px; left: 50px;">&times;</button>`
    parent.appendChild(elementToUpdate)
    document.getElementById(`${parentId}-closeButton`).addEventListener("click", (evt) => {
        parent.style.display = 'none'
        parent.innerHTML = ''
    })
    parent.style.display = 'block'
}

function findNearestMarketOpenDate(datesArray, comparisonDate) {
    let closest = datesArray[0];
    let closestDiff = Math.abs(new Date(closest) - new Date(comparisonDate));

    for (let i = 1; i < datesArray.length; i++) {
        const diff = Math.abs(new Date(datesArray[i]) - new Date(comparisonDate));

        // If the current difference is larger than the smallest difference found so far,
        // and we know the array is sorted, we can stop iterating.
        if (diff > closestDiff) {
            break;
        }

        closestDiff = diff;
        closest = datesArray[i];
    }

    return closest;
}
