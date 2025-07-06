let stationId = null;
let pollInterval = 20000; // 20 seconds
let pollingTimeout = null;

/**
* Retrieves the HTML form element with the ID 'stationForm'.
* @type {HTMLFormElement|null}
*/
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

/**
 * Polls the server for updates on the current station.
 * Sends a POST request with the station ID to the '/poll_station' endpoint.
 * On success, updates the song information display if a new song is returned.
 * Schedules the next poll after a specified interval.
 * Handles errors by logging them and rescheduling the poll.
 *
 * @function
 * @returns {void}
 */
function pollStation() {
    if (!stationId) return;

    fetch('/poll_station', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ station_id: stationId })
    })
    .then(response => response.json())
    .then(data => {
        const songInfoDiv = document.getElementById('songInfo');
        if (data.song) {
            songInfoDiv.innerHTML = `
                <img src="${data.song.Image}" alt="Song Image" width="200"><br>
                <strong>${data.song.Title}</strong> by ${data.song.Artist} - Added to Queue
            `;
        } else {
            songInfoDiv.textContent = 'No song found.';
        }

        pollingTimeout = setTimeout(pollStation, pollInterval);
    })
    .catch(error => {
        console.error('Polling error:', error);
        pollingTimeout = setTimeout(pollStation, pollInterval);
    });
}

