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