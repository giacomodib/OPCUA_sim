let chart;
let selectedMetric = 'temperature';
const maxDataPoints = 60;

const data = {
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

function updateChart(newValue) {
    if (!chart) return;

    const now = new Date();
    data.labels.push(now.toLocaleTimeString());
    data.datasets[0].data.push(newValue);

    if (data.labels.length > maxDataPoints) {
        data.labels.shift();
        data.datasets[0].data.shift();
    }

    chart.update();
}

function updateMaterialInfo(materialData) {
    document.getElementById('tensileStrength').textContent = materialData.tensile_strength || '0';
    document.getElementById('cuttingSpeed').textContent = materialData.cutting_speed?.toFixed(1) || '0';
    document.getElementById('feedRate').textContent = materialData.feed_rate?.toFixed(3) || '0';
    document.getElementById('pieces').textContent = materialData.pieces || '0';
}

function updateAlarmStatus(machineData) {
    const alarmStatusElement = document.getElementById('alarmStatus');
    const alarmMessageElement = document.getElementById('alarmMessage');

    if (machineData.state === 'allarme') {
        alarmStatusElement.className = 'alarm-active';
        alarmMessageElement.textContent = `Allarme: ${machineData.alarm_type || 'Sconosciuto'}`;
        alarmMessageElement.style.display = 'block';
    } else if (machineData.state === 'errore') {
        alarmStatusElement.className = 'error-active';
        alarmMessageElement.textContent = `Errore: ${machineData.alarm_type || 'Sconosciuto'}`;
        alarmMessageElement.style.display = 'block';
    } else {
        alarmStatusElement.className = 'no-alarm';
        alarmMessageElement.style.display = 'none';
    }
}

function fetchData() {
    fetch('/api/data')
        .then(response => response.json())
        .then(data => {
            if (data) {
                updateChart(data[selectedMetric]);
                updateMaterialInfo(data);
                updateAlarmStatus(data);
                document.getElementById('stateSelect').value = data.state;
                document.getElementById('materialSelect').value = data.material;
                document.getElementById('sectionSelect').value = data.section;
            }
        })
        .catch(error => console.error('Error fetching data:', error));
}

function sendPostRequest(url, requestBody) {
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
    })
    .catch(error => console.error('Error sending data to ' + url, error));
}

function updateMaterialSettings(material) {
    sendPostRequest('/api/set_material', { material });
}

function updateSectionSettings(section) {
    sendPostRequest('/api/set_section', { section });
}

function setAlarm(alarmType) {
    sendPostRequest('/api/set_alarm', { alarm: alarmType });
}

function resetAlarm() {
    sendPostRequest('/api/reset_alarm', {});
}

document.addEventListener('DOMContentLoaded', function() {
    initChart();

    setTimeout(() => {
        fetchData();
        setInterval(fetchData, 1000);
    }, 1000);

    document.getElementById('chartSelect').addEventListener('change', function(e) {
        selectedMetric = e.target.value;
        data.datasets[0].data = [];
        data.labels = [];

        const labels = {
            'temperature': 'Temperatura (°C)',
            'consumption': 'Consumo Energetico (W)',
            'pieces': 'Conteggio Pezzi'
        };

        data.datasets[0].label = labels[selectedMetric];
        chart.update();
    });

    document.getElementById('stateSelect').addEventListener('change', function(e) {
        sendPostRequest('/api/set_state', { state: e.target.value });
    });

    // Allarmi
    document.getElementById('setAlarmButton')?.addEventListener('click', function() {
        const alarmType = document.getElementById('alarmSelect').value;
        setAlarm(alarmType);
    });

    document.getElementById('resetAlarmButton')?.addEventListener('click', function() {
        resetAlarm();
    });

    // Safety barrier toggle
    document.getElementById('safetyBarrierToggle')?.addEventListener('change', function(e) {
        sendPostRequest('/api/set_safety_barrier', { is_open: e.target.checked });
    });

    // Material and Section Change Events
    document.getElementById('materialSelect')?.addEventListener('change', function() {
        updateMaterialSettings(this.value);
    });

    document.getElementById('sectionSelect')?.addEventListener('change', function() {
        updateSectionSettings(this.value);
    });
});
