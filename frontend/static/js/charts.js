let chart;
let selectedMetric = 'temperature';
const maxDataPoints = 60;
let data = {
    labels: [],
    datasets: [{
        label: 'Temperature (°C)',
        data: [],
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1
    }]
};

function initChart() {
    const ctx = document.getElementById('monitorChart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            animation: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

async function fetchData() {
    try {
        const response = await fetch('/api/opcua/values');
        const data = await response.json();
        if (data) {
            updateChart(data[selectedMetric]);
            document.getElementById('cuttingSpeed').textContent = data.cutting_speed?.toFixed(1) || '0';
            document.getElementById('feedRate').textContent = data.feed_rate?.toFixed(3) || '0';
            document.getElementById('pieces').textContent = data.pieces || '0';
        }
    } catch (error) {
        console.error('Error fetching OPC-UA data:', error);
    }
}

function updateChart(newValue) {
    const now = new Date();
    data.labels.push(now.toLocaleTimeString());
    data.datasets[0].data.push(newValue);

    if (data.labels.length > maxDataPoints) {
        data.labels.shift();
        data.datasets[0].data.shift();
    }

    chart.update('none');
}

document.addEventListener('DOMContentLoaded', function() {
    initChart();
    setInterval(fetchData, 1000);

    document.getElementById('setAlarmButton').addEventListener('click', async function() {
        const alarmType = document.getElementById('alarmSelect').value;
        try {
            await fetch('/api/opcua/set_alarm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ alarm: alarmType })
            });
        } catch (error) {
            console.error('Error setting alarm via OPC-UA:', error);
        }
    });
});
