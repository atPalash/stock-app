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
    var timestamp = time
    if (time.includes(":")) {
        timestamp = timestamp.replace(" ", "T")
        timestamp = timestamp + "+05:30"
        timestamp = new Date(timestamp)
        timestamp = timestamp.getTime()
        return timestamp
    }
    return timestamp
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

function addListToDiv(divId, options) {
    // Create the unordered list element
    const ul = document.createElement('ul');
    if ('id' in options) {
        ul.setAttribute('id', options['id'])
    }

    // Create and append the list items to the unordered list
    for (var key in options['list']) {
        if (options['list'][key]) {
            const li = document.createElement('li');
            li.textContent = key;
            ul.appendChild(li);
        }
    }

    // Append the unordered list to the body of the page
    document.getElementById(divId).appendChild(ul);
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