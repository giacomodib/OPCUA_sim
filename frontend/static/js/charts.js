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

function updateChart(newValue) {
    if (chart === undefined) return;

    const now = new Date();
    data.labels.push(now.toLocaleTimeString());
    data.datasets[0].data.push(newValue);

    if (data.labels.length > maxDataPoints) {
        data.labels.shift();
        data.datasets[0].data.shift();
    }

    chart.update('none');
}

function updateMachineStatus(data) {
    // Update machine info
    document.getElementById('cuttingSpeed').textContent = data.cutting_speed?.toFixed(1) || '0';
    document.getElementById('feedRate').textContent = data.feed_rate?.toFixed(3) || '0';
    document.getElementById('pieces').textContent = data.pieces || '0';
    document.getElementById('tensileStrength').textContent = data.tensile_strength || '0';
    document.getElementById('bladeWear').textContent = (data.blade_wear || 0).toFixed(1);
    document.getElementById('coolantLevel').textContent = (data.coolant_level || 0).toFixed(1);
}

function updateAlarmStatus(data) {
    const alarmStatusElement = document.getElementById('alarmStatus');
    const alarmMessageElement = document.getElementById('alarmMessage');

    if (data.state === 'allarme') {
        alarmStatusElement.className = 'alert alert-danger';
        let alarmMessage = data.alarm_type || 'Unknown';
        alarmMessageElement.textContent = `Alarm: ${alarmMessage}`;
        alarmMessageElement.style.display = 'block';
    } else if (data.state === 'errore') {
        alarmStatusElement.className = 'alert alert-warning';
        alarmMessageElement.textContent = `Error: ${data.alarm_type || 'Unknown'}`;
        alarmMessageElement.style.display = 'block';
    } else {
        alarmStatusElement.className = 'alert alert-success';
        alarmStatusElement.textContent = 'System Operational';
        alarmMessageElement.style.display = 'none';
    }
}

function fetchData() {
    fetch('/api/machine_status')
        .then(response => response.json())
        .then(data => {
            if (data) {
                // updates
                updateChart(data.temperature);
                updateMachineStatus(data);
                updateAlarmStatus(data);      

                document.getElementById('stateSelect').value = data.state;
                document.getElementById('materialSelect').value = data.material;
                document.getElementById('sectionSelect').value = data.section;
            }
        })
        .catch(error => console.error('Errore durante il recupero dei dati:', error));
}
function updateMachineSettings(endpoint, data) {
    fetch(`/api/${endpoint}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .catch(error => console.error(`Error updating ${endpoint}:`, error));
}

document.addEventListener('DOMContentLoaded', function() {
    initChart();

    // Start data polling
    setTimeout(() => {
        fetchData();
        setInterval(fetchData, 1000);
    }, 1000);

    // Chart metric selection
    document.getElementById('chartSelect').addEventListener('change', function(e) {
        selectedMetric = e.target.value;
        data.datasets[0].data = [];
        data.labels = [];

        const labels = {
            'temperature': 'Temperature (°C)',
            'consumption': 'Power Consumption (W)',
            'blade_wear': 'Blade Wear (%)',
            'coolant_level': 'Coolant Level (%)'
        };

        data.datasets[0].label = labels[selectedMetric];
        chart.update();
    });

    // Machine state control
    document.getElementById('stateSelect').addEventListener('change', function(e) {
        updateMachineSettings('set_state', { state: e.target.value });
    });

    // Material settings
    document.getElementById('materialSelect').addEventListener('change', function(e) {
        updateMachineSettings('set_material', { material: e.target.value });
    });

    // Section settings
    document.getElementById('sectionSelect').addEventListener('change', function(e) {
        updateMachineSettings('set_section', { section: e.target.value });
    });

    // Alarm controls
    document.getElementById('setAlarmButton')?.addEventListener('click', function() {
        const alarmType = document.getElementById('alarmSelect').value;
        updateMachineSettings('set_alarm', { alarm: alarmType });
    });

    document.getElementById('resetAlarmButton')?.addEventListener('click', function() {
        updateMachineSettings('reset_alarm', {});
    });

    // Safety barrier toggle
    document.getElementById('safetyBarrierToggle')?.addEventListener('change', function(e) {
        if (e.target.checked) {
            updateMachineSettings('set_alarm', { alarm: 'SAFETY_BARRIER' });
        } else {
            updateMachineSettings('reset_alarm', {});
        }
    });
});