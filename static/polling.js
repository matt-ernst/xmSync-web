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

    .then(async response => {
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Polling request failed (${response.status}): ${errorText.slice(0, 200)}`);
        }

        const contentType = response.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) {
            const responseText = await response.text();
            throw new Error(`Expected JSON response, received: ${responseText.slice(0, 200)}`);
        }

        return response.json();
    })
    .then(data => {
        const songInfoDiv = document.getElementById('songInfo');
        if (data.song) {
            songInfoDiv.innerHTML = `
                <img src="${data.song.Image}" alt="Song Image" width="200"><br>
                <strong><em>${data.song.Title}</em></strong><br>${data.song.Artist}<br><em>Added to Queue</em>
            `;
            if (data.new_song_added) {
                showToast(data.song);
            }
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

function showToast(song) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
        <img class="toast-art" src="${song.Image}" alt="">
        <div class="toast-body">
            <div class="toast-label">Added to Queue</div>
            <div class="toast-title">${song.Title}</div>
            <div class="toast-artist">${song.Artist}</div>
        </div>
    `;
    container.appendChild(toast);

    setTimeout(function () {
        toast.classList.add('toast-out');
        toast.addEventListener('animationend', function () { toast.remove(); }, { once: true });
    }, 3500);
}