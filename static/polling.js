let stationId = null;
let pollInterval = 20000; // 20 seconds
let pollingTimeout = null;

window.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('stationForm');
    if (!form) return;

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        stationId = document.getElementById('stationInput').value;
        document.getElementById('songInfo').innerText = "Polling station: " + stationId;
        if (pollingTimeout) clearTimeout(pollingTimeout);
        pollStation();
    });
});

function pollStation() {
    if (!stationId) return;

    fetch('/poll_station', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ station_id: stationId })
    })
        .then(response => response.json())
        .then(data => {
            // Update song info display
            if (data.song) {
                document.getElementById('songInfo').innerText =
                    `Now Playing: ${data.song.Title} by ${data.song.Artist}`;
            }

            //add song to log

            pollingTimeout = setTimeout(pollStation, pollInterval);
        })
        .catch(error => {
            console.error('Polling error:', error);
            pollingTimeout = setTimeout(pollStation, pollInterval);
        });
}
