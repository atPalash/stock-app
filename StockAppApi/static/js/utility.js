async function apiPost(endPoint, query) {
    var response = await fetch(`http://localhost:8087/${endPoint}`, {
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
    var response = await fetch(`http://localhost:8087/${endPoint}`, {
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
        // time zone, also when DST is applied
        const offset = 10800      
        return Date.parse(time) / 1000 + offset
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

function addListToDiv(parentId, list, eventHandler=null, metaData=null) {
    // Create the unordered list element
    const ul = document.createElement('ul');
    ul.setAttribute('id', `${parentId}-list`)
    ul.setAttribute('style', "margin-top: 0; margin-bottom: 0;")

    for (let ticker in list) {
        const li = document.createElement('li');
        li.textContent = ticker;
        li.style.color = "black"
        li.setAttribute('meta-data', JSON.stringify(list[ticker]))
        ul.appendChild(li);
    }

    // Append the unordered list to the body of the page
    document.getElementById(parentId).appendChild(ul);
    ul.addEventListener('mouseover', function(event) {
        if (event.target.matches('li')) {
          event.target.style.cursor = 'pointer';
        }
      });
    if(eventHandler!=null) {
        ul.addEventListener("click", (event) => {
            eventHandler(event)
        })
    }
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

function changeSelection(id, index, detail=null) {
    var select = document.getElementById(id)
    select.selectedIndex = index
    var event = new Event('change');
    event.detail = detail
    select.dispatchEvent(event);
}

function popUpSelection(id, index, detail=null) {
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
