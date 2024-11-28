const ctx = document.getElementById('temperatureChart').getContext('2d');
const temperatureChart = new Chart(ctx, {
    type: 'line', // Change chart type to line
    data: {
        datasets: [{
            label: 'Temperature (°C)',
            data: [],
            backgroundColor: 'rgba(0, 130, 0, 0.12)', // Adjust background color for line chart
            borderColor: 'rgba(6, 248, 43, 0.85)', // Line color
            fill: false, // Do not Fill under the line
        }]
    },
    options: {
        scales: {
            x: {
                title: { display: true, text: 'Timestamp', color: 'white' },
                type: 'time', // Make sure to handle timestamps as needed
                time: {
                    unit: 'minute'
                },
                ticks: {
                    color: 'white' // Change x-axis values color
                }
            },
            y: {
                title: { display: true, text: 'Temperature (°C)', color: 'white' },
                beginAtZero: false,
                ticks: {
                    color: 'white' // Change y-axis values color
                }
            }
        }
    }
});

// Function to fetch temperature data
async function fetchTemperatureData() {
    try {
        const response = await fetch('/data');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        const temperatures = data.map(entry => ({
            x: new Date(entry.timestamp),
            y: entry.temp
        }));

        temperatureChart.data.datasets[0].data = temperatures;
        temperatureChart.update();

        if (data.length > 0) {
            const latestTemp = data[data.length - 1].temp;
            document.getElementById('currentTemp').innerText = `Current Temperature: ${latestTemp}°C`;
        } else {
            document.getElementById('currentTemp').innerText = 'No temperature data available.';
        }
    } catch (error) {
        console.error('Error fetching temperature data:', error);
        document.getElementById('currentTemp').innerText = 'Error fetching temperature data.';
    }
}

// Fetch the latest temperature on page load
fetchTemperatureData();

// Update data every minute
setInterval(fetchTemperatureData, 60000);

// New functionality for starting/stopping data collection and saving data
let dataCollectionInterval;
let isCollectingData = false;

function toggleDataCollection() {
    const button = document.getElementById('toggleDataCollection');
    if (isCollectingData) {
        clearInterval(dataCollectionInterval);
        button.innerText = 'Start Data Collection';
        isCollectingData = false;
        document.getElementById('downloadLink').style.display = 'block';
    } else {
        // Reset chart data
        temperatureChart.data.datasets[0].data = [];
        temperatureChart.update();

        fetchTemperatureData(); // Fetch data immediately
        dataCollectionInterval = setInterval(fetchTemperatureData, 60000); // Fetch data every minute
        button.innerText = 'Stop Data Collection';
        isCollectingData = true;
        document.getElementById('downloadLink').style.display = 'none';
    }
}

async function saveData() {
    const response = await fetch('/save_data', { method: 'POST' });
    const result = await response.json();
    alert(result.message);
}

document.getElementById('targetTempForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    const targetTemp = document.getElementById('target_temp').value;
    if (targetTemp) {
        try {
            const response = await fetch('/set_target_temp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ target_temp: targetTemp })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            document.getElementById('message').innerText = result.message;
            updateSystemStatus();
        } catch (error) {
            console.error('Error:', error);
            document.getElementById('message').innerText = 'An error occurred. Please try again.';
        }
    } else {
        alert('Please enter a valid target temperature.');
    }
});

async function updateSystemStatus() {
    const targetTemp = document.getElementById('target_temp').value;
    try {
        const response = await fetch(`/system_status?target_temp=${targetTemp}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        const systemStatusElement = document.getElementById('systemStatus');
        systemStatusElement.innerText = `System is ${result.status}`;

        if (result.status === 'Heating') {
            systemStatusElement.style.color = 'red';
        } else if (result.status === 'Cooling') {
            systemStatusElement.style.color = 'blue';
        } else {
            systemStatusElement.style.color = 'white';
        }
    } catch (error) {
        console.error('Error updating system status:', error);
        document.getElementById('systemStatus').innerText = 'Error updating system status.';
        document.getElementById('systemStatus').style.color = 'white';
    }
}

fetchTemperatureData();
setInterval(fetchTemperatureData, 60000);
setInterval(updateSystemStatus, 60000);