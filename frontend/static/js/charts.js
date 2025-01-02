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

function updateMaterialInfo(data) {
    document.getElementById('tensileStrength').textContent = data.tensile_strength || '0';
    document.getElementById('cuttingSpeed').textContent = data.cutting_speed?.toFixed(1) || '0';
    document.getElementById('feedRate').textContent = data.feed_rate?.toFixed(3) || '0';
    document.getElementById('pieces').textContent = data.pieces || '0';
}

function fetchData() {
    fetch('/api/data')
        .then(response => response.json())
        .then(data => {
            if (data) {
                updateChart(data[selectedMetric]);
                updateMaterialInfo(data);
                document.getElementById('stateSelect').value = data.state;
                document.getElementById('materialSelect').value = data.material;
                document.getElementById('sectionSelect').value = data.section;
            }
        })
        .catch(error => console.error('Error fetching data:', error));
}

function updateMaterialSettings(material) {
    fetch('/api/set_material', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            material: material
        })
    })
    .catch(error => console.error('Error setting material:', error));
}

function updateSectionSettings(section) {
    fetch('/api/set_section', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            section: section
        })
    })
    .catch(error => console.error('Error setting section:', error));
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
        fetch('/api/set_state', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                state: e.target.value
            })
        })
        .catch(error => console.error('Error setting state:', error));
    });

    const materialSelect = document.getElementById('materialSelect');
    const sectionSelect = document.getElementById('sectionSelect');

    // Funzione per gestire l'aggiornamento del materiale
    function handleMaterialChange() {
        const material = materialSelect.value;
        updateMaterialSettings(material);
    };


    // Funzione per gestire l'aggiornamento della sezione
    function handleSectionChange() {
        const section = sectionSelect.value;
        updateSectionSettings(section);
    };


    materialSelect.addEventListener('change', handleMaterialChange);
    sectionSelect.addEventListener('change', handleSectionChange);

});