import asyncio
import argparse
from source.device.boiler import BoilerBacnetDevice
from source.simulation.simulation import SimulationContext
from source.simulation.states import InitializeState

def positive_int(value):
    """Helper function for argparse to ensure the number is positive."""
    num_value = int(value)
    if num_value <= 0:
        raise argparse.ArgumentTypeError(f"{value} is not a positive integer")
    return num_value

async def main(ip: str, port: int, device_id: int, simulation_mode: int, initial_setpoint: float, speed_factor: int):
    boiler = BoilerBacnetDevice(name="Boiler1", ip=ip, port=port, device_id=device_id)
    initial_state = InitializeState()
    try:
        await boiler.start()
        simulation_boiler = SimulationContext(boiler, initial_state, simulation_mode, initial_setpoint)
        await simulation_boiler.run_simulation(speed_factor)
    except KeyboardInterrupt:
        print("Stopping boiler...")
        await boiler.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Boiler simulation parameters")
    parser.add_argument("deviceIP", type=str, help="IP address of the device")
    parser.add_argument("devicePort", type=int, help="Port of the device")
    parser.add_argument("--deviceID", type=int, default=1, help="Optional device ID (default: 1)")
    parser.add_argument("--initial_setpoint", type=float, default=70.0, help="Initial set point (default: 70)")
    parser.add_argument("--simulation_mode", type=int, choices=[0, 1], default=0, help="Operation mode (default: 0)")
    parser.add_argument("--speed_factor", type=positive_int, default=1, help="Positive integer speed factor (default: 1)")

    args = parser.parse_args()

    asyncio.run(main(
        ip=args.deviceIP,
        port=args.devicePort,
        device_id=args.deviceID,
        simulation_mode=args.simulation_mode,
        initial_setpoint=args.initial_setpoint,
        speed_factor=args.speed_factor
    ))
