const ctx = document.getElementById('temperatureChart').getContext('2d');
const temperatureChart = new Chart(ctx, {
    type: 'line', // Change chart type to line
    data: {
        datasets: [{
            label: 'Temperature (°C)',
            data: [],
            backgroundColor: 'rgba(75, 192, 192, 0.2)', // Adjust background color for line chart
            borderColor: 'rgba(75, 192, 192, 1)', // Line color
            fill: true, // Fill under the line
        }]
    },
    options: {
        scales: {
            x: {
                title: { display: true, text: 'Timestamp' },
                type: 'time', // Make sure to handle timestamps as needed
                time: {
                    unit: 'minute'
                }
            },
            y: {
                title: { display: true, text: 'Temperature (°C)' },
                beginAtZero: false
            }
        }
    }
});

// Function to fetch temperature data
async function fetchTemperatureData() {
    const response = await fetch('/data');
    const data = await response.json();
    const temperatures = data.map(entry => ({
        x: new Date(entry.timestamp), // Parse timestamp as Date object
        y: entry.temp
    }));

    // Update chart data
    temperatureChart.data.datasets[0].data = temperatures;
    temperatureChart.update();

    // Update current temperature display
    if (data.length > 0) {
        const latestTemp = data[data.length - 1].temp;
        document.getElementById('currentTemp').innerText = `Current Temperature: ${latestTemp}°C`;
    } else {
        document.getElementById('currentTemp').innerText = 'No temperature data available.';
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
    if (targetTemp) {
        const response = await fetch(`/system_status?target_temp=${targetTemp}`);
        const result = await response.json();
        document.getElementById('systemStatus').innerText = `System is ${result.status}`;
    } else {
        document.getElementById('systemStatus').innerText = 'System is OFF';
    }
}

// Call updateSystemStatus periodically
setInterval(updateSystemStatus, 60000); // Update every minute