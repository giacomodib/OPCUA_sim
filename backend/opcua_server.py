import asyncio
from datetime import datetime
from asyncua import Server, ua
from backend.bandsaw_simulator import (
    BandSawSimulator, MachineState, AlarmType, SectionType
)


async def main():
    server = Server()
    await server.init()

    url = "opc.tcp://localhost:4841/freeopcua/server/"
    server.set_endpoint(url)
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

    uri = "http://examples/bandsaw"
    idx = await server.register_namespace(uri)

    objects = server.nodes.objects
    machine = await objects.add_object(idx, "BandSaw")

    # Initialize simulator
    simulator = BandSawSimulator()

    # Basic machine state variables
    state_var = await machine.add_variable(idx, "State", simulator.state.value, ua.VariantType.String)
    alarm_type_var = await machine.add_variable(idx, "AlarmType", simulator.alarm.value, ua.VariantType.String)

    # Production parameters
    pieces_var = await machine.add_variable(idx, "Pieces", simulator.pieces, ua.VariantType.Int64)
    scrap_pieces_var = await machine.add_variable(idx, "ScrapPieces", simulator.scrap_pieces, ua.VariantType.Int64)
    pieces_per_hour_var = await machine.add_variable(idx, "PiecesPerHour", simulator.pieces_per_hour,
                                                     ua.VariantType.Double)

    # Machine parameters
    material_var = await machine.add_variable(idx, "Material", simulator.material, ua.VariantType.String)
    section_var = await machine.add_variable(idx, "Section", simulator.section, ua.VariantType.String)
    section_type_var = await machine.add_variable(idx, "SectionType", simulator.section_type.value,
                                                  ua.VariantType.String)
    cutting_angle_var = await machine.add_variable(idx, "CuttingAngle", simulator.cutting_angle, ua.VariantType.Double)

    # Cutting parameters
    cutting_speed_var = await machine.add_variable(idx, "CuttingSpeed", simulator.cutting_speed, ua.VariantType.Double)
    feed_rate_var = await machine.add_variable(idx, "FeedRate", simulator.feed_rate, ua.VariantType.Double)
    recommended_speed_var = await machine.add_variable(idx, "RecommendedSpeed", simulator.recommended_cutting_speed,
                                                       ua.VariantType.Double)
    recommended_feed_var = await machine.add_variable(idx, "RecommendedFeedRate", simulator.recommended_feed_rate,
                                                      ua.VariantType.Double)

    # Machine health
    temp_var = await machine.add_variable(idx, "Temperature", simulator.temperature, ua.VariantType.Double)
    consumption_var = await machine.add_variable(idx, "PowerConsumption", simulator.consumption, ua.VariantType.Double)
    blade_wear_var = await machine.add_variable(idx, "BladeWear", simulator.blade_wear, ua.VariantType.Double)
    coolant_level_var = await machine.add_variable(idx, "CoolantLevel", simulator.coolant_level, ua.VariantType.Double)

    # Make variables writable
    writable_vars = [
        state_var, alarm_type_var, material_var, section_var,
        section_type_var, cutting_angle_var, cutting_speed_var, feed_rate_var
    ]
    for var in writable_vars:
        await var.set_writable()

    print(f"OPC-UA Server started at {url}")

    try:
        async with server:
            while True:
                # Handle state changes
                new_state = await state_var.get_value()
                if new_state != simulator.state.value:
                    try:
                        simulator.state = MachineState(new_state)
                        simulator.last_state_change = datetime.now()
                        print(f"State changed to: {new_state}")
                    except ValueError:
                        print(f"Invalid state received: {new_state}")

                # Handle alarm changes
                new_alarm = await alarm_type_var.get_value()
                if new_alarm != simulator.alarm.value:
                    try:
                        simulator.alarm = AlarmType(new_alarm)
                        if simulator.alarm != AlarmType.NONE:
                            simulator.state = MachineState.ALARM
                    except ValueError:
                        print(f"Invalid alarm type received: {new_alarm}")

                # Handle material parameter changes
                new_material = await material_var.get_value()
                new_section = await section_var.get_value()
                new_section_type = await section_type_var.get_value()
                if (new_material != simulator.material or
                        new_section != simulator.section or
                        new_section_type != simulator.section_type.value):
                    simulator.set_material_parameters(
                        material=new_material,
                        section=new_section,
                        section_type=SectionType(new_section_type)
                    )

                # Handle cutting parameter changes
                new_speed = await cutting_speed_var.get_value()
                new_feed = await feed_rate_var.get_value()
                new_angle = await cutting_angle_var.get_value()
                if (new_speed != simulator.cutting_speed or
                        new_feed != simulator.feed_rate or
                        new_angle != simulator.cutting_angle):
                    simulator.set_cutting_parameters(
                        cutting_speed=new_speed,
                        feed_rate=new_feed,
                        cutting_angle=new_angle
                    )

                # Update simulator state
                simulator.update_state()

                # Write all updated values back to OPC-UA server
                await state_var.write_value(simulator.state.value)
                await alarm_type_var.write_value(simulator.alarm.value)
                await pieces_var.write_value(simulator.pieces)
                await scrap_pieces_var.write_value(simulator.scrap_pieces)
                await pieces_per_hour_var.write_value(float(simulator.pieces_per_hour)) #mettere float in questa var              await cutting_speed_var.write_value(simulator.cutting_speed)
                await feed_rate_var.write_value(simulator.feed_rate)
                await recommended_speed_var.write_value(simulator.recommended_cutting_speed)
                await recommended_feed_var.write_value(simulator.recommended_feed_rate)
                await temp_var.write_value(simulator.temperature)
                await consumption_var.write_value(simulator.consumption)
                await blade_wear_var.write_value(simulator.blade_wear)
                await coolant_level_var.write_value(simulator.coolant_level)

                await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nShutdown signal received. Stopping server...")
