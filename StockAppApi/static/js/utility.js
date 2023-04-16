async function apiCall(query) {
    var response = await fetch('http://localhost:8087/ohlc', {
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
        var listenerElement = document.getElementById(evnt)
        var val = options["events"][evnt]
        listenerElement.addEventListener(val["type"], val["callback"]);
    }
}

function parseJSON(jsonString) {
    var thisJson = {}
    try {
        var jObj = JSON.parse(jsonString)
        for(var key in jObj){
            thisJson[key] = parseJSON(jObj[key])
        };
    } catch (error) {
        for(var key in jsonString){
            thisJson[key] = parseJSON(jObj[key])
        };
    }
    return thisJson;
  }