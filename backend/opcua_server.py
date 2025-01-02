import asyncio
from datetime import datetime
from asyncua import Server, ua
from backend.bandsaw_simulator import BandSawSimulator, MachineState, calculate_feed_rate, calculate_cutting_speed


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

    state_var = await machine.add_variable(idx, "State", "inattiva", ua.VariantType.String)
    speed_var = await machine.add_variable(idx, "CuttingSpeed", simulator.cutting_speed, ua.VariantType.Double)
    feed_rate_var = await machine.add_variable(idx, "FeedRate", simulator.feed_rate, ua.VariantType.Double)
    pieces_var = await machine.add_variable(idx, "Pieces", 0, ua.VariantType.Int64)
    consumption_var = await machine.add_variable(idx, "Consumption", 1000.0, ua.VariantType.Double)
    material_var = await machine.add_variable(idx, "Material", simulator.material, ua.VariantType.String)
    section_var = await machine.add_variable(idx, "Section", simulator.section, ua.VariantType.String)
    temp_var = await machine.add_variable(idx, "Temperature", 20.0, ua.VariantType.Double)

    for var in [state_var, speed_var, feed_rate_var, pieces_var, consumption_var, material_var, section_var, temp_var]:
        await var.set_writable()

    print(f"Server OPC-UA avviato all'indirizzo {url}")

    try:
        async with server:
            while True:
                new_state = await state_var.get_value()
                if new_state != simulator.state.value:
                    try:
                        simulator.state = MachineState(new_state)
                        simulator.last_state_change = datetime.now()
                        print(f"Stato cambiato esternamente a: {new_state}")
                    except ValueError:
                        print(f"Stato non valido ricevuto: {new_state}")

                new_material = await material_var.get_value()
                new_section = await section_var.get_value()
                if new_material != simulator.material or new_section != simulator.section:
                    simulator.material = new_material
                    simulator.section = new_section
                    simulator.cutting_speed = calculate_cutting_speed(simulator.material, simulator.section)
                    simulator.feed_rate = calculate_feed_rate(simulator.material, simulator.section)

                simulator.update_state()

                await state_var.write_value(simulator.state.value)
                await speed_var.write_value(float(simulator.cutting_speed))
                await feed_rate_var.write_value(float(simulator.feed_rate))
                await pieces_var.write_value(int(simulator.pieces))
                await consumption_var.write_value(float(simulator.consumption))
                await material_var.write_value(simulator.material)
                await section_var.write_value(simulator.section)
                await temp_var.write_value(float(simulator.temperature))

                await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nRicevuto segnale di interruzione. Arresto del server...")

if __name__ == "__main__":
    asyncio.run(main())