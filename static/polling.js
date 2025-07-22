let stationId = null;
let pollInterval = 30000; // 30 seconds
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
        stationId = document.getElementById('stationDropdown').value;
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
    if (!stationId){
        console.warn('No station selected for polling.');
        return;
    }

    console.log('Polling station:', stationId);

    fetch(`${window.location.origin}/poll_station`, {
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
                <strong><em>${data.song.Title}</em></strong><br>${data.song.Artist}<br><em>Added to Queue</em>
            `;
        } else {
            console.log(data)
            songInfoDiv.textContent = 'No Playable Song Found, Try a Different Station';
        }

        pollingTimeout = setTimeout(pollStation, pollInterval);
    })
    .catch(error => {
        console.error('Polling error:', error);
        pollingTimeout = setTimeout(pollStation, pollInterval);
    });
}