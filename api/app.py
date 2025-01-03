# app.py
from flask import Flask, render_template, jsonify, request
import logging
from backend.opcua_client import OPCUAClient
from backend.bandsaw_simulator import materials_data, AlarmType, MachineState

app = Flask(__name__,
            static_folder='../frontend/static',
            template_folder='../frontend/templates')

client = OPCUAClient()

# Configura il logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)  # Mostrerà solo gli errori, non le richieste normali

@app.route('/')
def index():
    return render_template('dashboard.html')


@app.route('/api/data')
def get_data():
    def async_get_data():
        async def fetch():
            try:
                state = await client.get_node_value("ns=2;i=2")
                cutting_speed = await client.get_node_value("ns=2;i=3")
                feed_rate = await client.get_node_value("ns=2;i=4")
                pieces = await client.get_node_value("ns=2;i=5")
                consumption = await client.get_node_value("ns=2;i=6")
                material = await client.get_node_value("ns=2;i=7")
                section = await client.get_node_value("ns=2;i=8")
                temperature = await client.get_node_value("ns=2;i=9")
                alarm_type = await client.get_node_value("ns=2;i=10")




                # Get material data from materials_data dictionary
                material_info = materials_data.get(material, {})
                tensile_strength = material_info.get('tensile_strength', 0)

                return {
                    'state': state if state is not None else 'inattiva',
                    'cutting_speed': float(cutting_speed) if cutting_speed is not None else 0,
                    'feed_rate': float(feed_rate) if feed_rate is not None else 0,
                    'pieces': int(pieces) if pieces is not None else 0,
                    'consumption': float(consumption) if consumption is not None else 0,
                    'material': material,
                    'section': section,
                    'temperature': float(temperature) if temperature is not None else 0,
                    'tensile_strength': tensile_strength,
                    'alarm_type': alarm_type if alarm_type is not None else AlarmType.NONE.value

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
                    'tensile_strength': 0
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
        # Prima imposta lo stato della macchina su "allarme"
        state_success = client.run_async(
            client.set_node_value("ns=2;i=2", MachineState.ALARM.value)
        )

        # TODO: Aggiungere un nodo OPC UA per il tipo di allarme
        # Per ora ritorniamo solo il successo del cambio di stato
        return state_success

    success = async_set_alarm()
    return jsonify({'success': success})


@app.route('/api/reset_alarm', methods=['POST'])
def reset_alarm():
    def async_reset_alarm():
        # Riporta la macchina allo stato inattivo
        state_success = client.run_async(
            client.set_node_value("ns=2;i=2", MachineState.INACTIVE.value)
        )

        # TODO: Resettare anche il nodo del tipo di allarme quando verrà aggiunto
        return state_success

    success = async_reset_alarm()
    return jsonify({'success': success})