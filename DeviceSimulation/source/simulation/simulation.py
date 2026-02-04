import datetime
import aiohttp
import asyncio
from datetime import datetime
from .states import State
from ..device.boiler import BoilerBacnetDevice

WEB_SERVER_URL = "http://localhost:8099/device/upload"
EXAMPLE_API_KEY = "EXAMPLE_API_KEY"


# --- SIMULATION ----
class SimulationContext:
    def __init__(self, device: BoilerBacnetDevice, initial_state: State, simulation_mode: int = 0, initial_setpoint: float = 25):
        self.state = initial_state
        self.device = device
        self.simulation_mode = simulation_mode

        self.capacity = 300
        self.potenza = 210
        self.ambient_temperature = 25
        self.setpoint = initial_setpoint

        self.interval_send_data = 10
        self.timer = 0

        # --- NEW ATTRIBUTES TO HANDLE ERRORS ---
        self.consecutive_errors = 0
        self.max_errors = 5  # stop sending API requests after 5 consecutive errors
        self.api_task = None

    async def run_simulation(self, simulation_speed: int):
        async with aiohttp.ClientSession() as session:
            while True:
                self.state.handle(self, simulation_speed)

                if self.device.get_device_operating_status() != 10:
                    self.device.increase_power_seconds()

                if self.device.get_burner_status():
                    self.device.increase_burner_seconds()

                # --- SEND DATA ONLY IF WE HAVE NOT EXCEEDED ERROR LIMIT ---
                if self.timer >= self.interval_send_data and self.consecutive_errors < self.max_errors:
                    if self.api_task is None or self.api_task.done():
                        self.api_task = asyncio.create_task(self.send_data_to_api(session))
                    self.timer = 0

                self.timer += simulation_speed
                await asyncio.sleep(1)

    async def send_data_to_api(self, session: aiohttp.ClientSession):
        print("Sending data to API")

        data = {
            "device_id": self.device.get_device_id(),
            "timestamp": datetime.now().isoformat(),
            "operation_mode": self.device.get_device_operating_status(),
            "supply_temp": self.device.get_supply_temperature(),
            "return_temp": self.device.get_return_temperature(),
            "outlet_pressure": self.device.get_outlet_pressure(),
            "inlet_pressure": self.device.get_inlet_pressure(),
            "instant_power": self.device.get_instant_power(),
            "pump_status": self.device.get_pump_status(),
            "error_message": self.device.get_error_message()
        }

        try:
            # 4-second timeout for API request
            async with asyncio.timeout(4):
                async with session.post(WEB_SERVER_URL, json=data, headers={"Authorization": f"{EXAMPLE_API_KEY}"}) as response:
                    if response.status == 204:
                        print("Data sent successfully")
                        self.consecutive_errors = 0  # reset error counter
                    else:
                        print(f"Error sending data: {response.status}")
                        self.consecutive_errors += 1

        except asyncio.TimeoutError:
            print("Timeout: API too slow")
            self.consecutive_errors += 1
        except Exception as e:
            print(f"Error while sending data: {e}")
            self.consecutive_errors += 1

        if self.consecutive_errors >= self.max_errors:
            print(f"Exceeded error limit ({self.max_errors}). Stopping API calls.")
