import asyncio
from datetime import datetime
from asyncua import Server, ua
from backend.bandsaw_simulator import BandSawSimulator, MachineState, calculate_feed_rate, calculate_cutting_speed, \
    AlarmType


async def main():
    server = Server()
    await server.init()

    url = "opc.tcp://localhost:4841/freeopcua/server/"
    server.set_endpoint(url)
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

    uri = "http://examples/segatrice1"
    idx = await server.register_namespace(uri)

    objects = server.nodes.objects
    machine = await objects.add_object(idx, "BandSaw")

    simulator = BandSawSimulator()

    state_var = await machine.add_variable(idx, "State", simulator.state.value, ua.VariantType.String)
    speed_var = await machine.add_variable(idx, "CuttingSpeed", simulator.cutting_speed, ua.VariantType.Double)
    feed_rate_var = await machine.add_variable(idx, "FeedRate", simulator.feed_rate, ua.VariantType.Double)
    pieces_var = await machine.add_variable(idx, "Pieces", simulator.pieces, ua.VariantType.Int64)
    consumption_var = await machine.add_variable(idx, "Consumption", simulator.consumption, ua.VariantType.Double)
    material_var = await machine.add_variable(idx, "Material", simulator.material, ua.VariantType.String)
    section_var = await machine.add_variable(idx, "Section", simulator.section, ua.VariantType.String)
    temp_var = await machine.add_variable(idx, "Temperature", simulator.temperature, ua.VariantType.Double)
    alarm_type_var = await machine.add_variable(idx, "AlarmType", simulator.alarm.value, ua.VariantType.String)
    for var in [state_var, speed_var, feed_rate_var, pieces_var, consumption_var, material_var, section_var, temp_var, alarm_type_var]:
        await var.set_writable()

    print(f"Server OPC-UA avviato all'indirizzo {url}")

    try:
        async with server:
            while True:
                # Gestione aggiornamento stato macchina
                new_state = await state_var.get_value()
                if new_state != simulator.state.value:
                    try:
                        simulator.state = MachineState(new_state)
                        simulator.last_state_change = datetime.now()
                        print(f"Stato cambiato esternamente a: {new_state}")
                    except KeyError:
                        print(f"Stato non valido ricevuto: {new_state}")

                # Aggiornamento materiale e sezione
                new_material = await material_var.get_value()
                new_section = await section_var.get_value()
                if new_material != simulator.material or new_section != simulator.section:
                    simulator.material = new_material
                    simulator.section = new_section
                    simulator.cutting_speed = calculate_cutting_speed(simulator.material, simulator.section)
                    simulator.feed_rate = calculate_feed_rate(simulator.material, simulator.section)

                # Aggiorna stato simulatore
                simulator.update_state()

                # Scrittura valori aggiornati nel server OPC-UA
                await state_var.write_value(simulator.state.value)
                await speed_var.write_value(simulator.cutting_speed)
                await feed_rate_var.write_value(simulator.feed_rate)
                await pieces_var.write_value(simulator.pieces)
                await consumption_var.write_value(simulator.consumption)
                await material_var.write_value(simulator.material)
                await section_var.write_value(simulator.section)
                await temp_var.write_value(simulator.temperature)
                await alarm_type_var.write_value(simulator.alarm.value)

                await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nRicevuto segnale di interruzione. Arresto del server...")

if __name__ == "__main__":
    asyncio.run(main())
