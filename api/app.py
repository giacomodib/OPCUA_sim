# app.py
from flask import Flask, render_template, jsonify, request
import logging
from backend.opcua_client import OPCUAClient
from backend.bandsaw_simulator import materials_data, AlarmType, MachineState

app = Flask(__name__,
            static_folder='../frontend/static',
            template_folder='../frontend/templates')

client = OPCUAClient()

@app.route('/')
def index():
    return render_template('dashboard.html')


@app.route('/api/data')
def get_data():
    def async_get_data():
        async def fetch():
            try:
                status = await client.get_machine_status()
                return {
                    'state': status.get('state', 'inattiva'),
                    'cutting_speed': float(status.get('cutting_speed', 0)),
                    'feed_rate': float(status.get('feed_rate', 0)),
                    'pieces': int(status.get('pieces', 0)),
                    'consumption': float(status.get('power_consumption', 0)),
                    'material': 'Acciai al carbonio St 37/42',  # Replace with actual material logic
                    'section': '<100mm',  # Replace with actual section logic
                    'temperature': float(status.get('temperature', 0)),
                    'tensile_strength': 400,  # Replace with actual material logic
                    'alarm_type': status.get('alarm_type', AlarmType.NONE.value)
                }
            except Exception as e:
                print(f"Error fetching data: {e}")
                return {
                    'state': '',
                    'cutting_speed': 0,
                    'feed_rate': 0,
                    'pieces': 0,
                    'consumption': 0,
                    'material': '',
                    'section': '',
                    'temperature': 0,
                    'tensile_strength': 0,
                    'alarm_type': ''
                }

        return client.run_async(fetch())

    return jsonify(async_get_data())



@app.route('/api/set_state', methods=['POST'])
def set_state():
    new_state = request.json['state']

    def async_set_state():
        return client.run_async(client.set_node_value("ns=2;i=2", new_state))

    success = async_set_state()
    return jsonify({'success': success})

@app.route('/api/set_material', methods=['POST'])
def set_material():
    material = request.json['material']

    def async_set_material():
        return client.run_async(client.set_node_value("ns=2;i=7", material))

    success = async_set_material()
    return jsonify({'success': success})


@app.route('/api/set_section', methods=['POST'])
def set_section():
    section = request.json['section']

    def async_set_section():
        return client.run_async(client.set_node_value("ns=2;i=8", section))

    success = async_set_section()
    return jsonify({'success': success})


@app.route('/api/set_alarm', methods=['POST'])
def set_alarm():
    alarm_type = request.json.get('alarm')

    def async_set_alarm():
        # Imposta lo stato della macchina su "allarme"
        state_success = client.run_async(
            client.set_node_value("ns=2;i=2", MachineState.ALARM.value)
        )

        # Imposta il tipo di allarme
        alarm_success = client.run_async(
            client.set_node_value("ns=2;i=10", alarm_type)
        )

        return state_success and alarm_success

    success = async_set_alarm()
    return jsonify({'success': success})


@app.route('/api/reset_alarm', methods=['POST'])
def reset_alarm():
    def async_reset_alarm():
        # Riporta la macchina allo stato inattivo
        state_success = client.run_async(
            client.set_node_value("ns=2;i=2", MachineState.INACTIVE.value)
        )

        # Resetta il tipo di allarme a "nessun allarme"
        alarm_success = client.run_async(
            client.set_node_value("ns=2;i=10", AlarmType.NONE.value)
        )

        return state_success and alarm_success

    success = async_reset_alarm()
    return jsonify({'success': success})

@app.route('/api/machine_status', methods=['GET'])
def machine_status():
    try:
        status = client.run_async(client.get_machine_status())
        return jsonify(status)
    except Exception as e:
        logging.error(f"Errore durante il recupero dello stato macchina: {e}")
        return jsonify({'error': 'Impossibile recuperare lo stato della macchina'}), 500
