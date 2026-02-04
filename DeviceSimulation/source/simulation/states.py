import math
from abc import ABC, abstractmethod

# --- HELP FUNCTIONS ----
def instantaneous_pressure_variation(delta_temp) -> float:
    return delta_temp*0.011

def instantaneous_temperature_decrement(current_temperature, ambient_temperature) -> float:
    return (current_temperature - ambient_temperature) * (math.exp(-0.000625) - 1)

def instantaneous_temperature_increment(setpoint, current_temperature, ambient_temperature, context) -> float:
    diff_temp = setpoint - ambient_temperature
    k_cont = (context.potenza * 1000) / (context.capacity * 4186 * diff_temp)
    return ((setpoint * 1.20) - current_temperature) * (1 - math.exp(-k_cont))

# --- STATE CLASSES ----
class State(ABC):
    @abstractmethod
    def handle(self, context, step):
        pass

class OffState(State):
    def handle(self, context, step):
        device = context.device
        device.set_fan_speed(0)
        device.set_pump_status(False)
        device.set_flow_rate(0)
        device.set_instant_power(0)
        device.set_device_operating_status(8)

        print(f"Device OFF state:")

        command = device.get_boiler_command()
        if command == True:
            context.state = InitializeState()

class InitializeState(State):
    def __init__(self):
        self._timer = 0

    def handle(self, context, step):
        device = context.device
        command = device.get_boiler_command()

        # Simulating Error
        print(f"Device INITIAL state: {context.simulation_mode}")
        if context.simulation_mode == 1:
            device.set_inlet_pressure(1.3)
            device.set_outlet_pressure(1.1)

        if command == False:
            context.state = OffState()

        current_status = device.get_device_operating_status()
        inlet_pressure = device.get_inlet_pressure()
        outlet_pressure = device.get_outlet_pressure()

        if current_status != 7:
            print("Starting Boiler...")
            device.set_device_operating_status(7)
            device.set_service_mode(3)
            device.set_instant_power(0.05)
            device.set_supply_temperature(20)
            device.set_return_temperature(20)

        print(f"Device on InitializeState: Timer: {self._timer}")


        print("inlet pressure:", inlet_pressure)
        print("outlet pressure:", outlet_pressure)
        print("device required pressure", device.get_required_pressure())
        print((inlet_pressure or outlet_pressure) < device.get_required_pressure())
        if inlet_pressure < device.get_required_pressure() or outlet_pressure < device.get_required_pressure():
            context.state = ErrorState()

        # TURN ON BOILER
        if self._timer >= 4:
            device.set_device_operating_status(6)
            device.set_air_temperature(context.ambient_temperature)
            device.set_supply_setpoint(context.setpoint)
            device.set_flow_rate(4.82)
            device.set_inlet_pressure(2.3)
            device.set_outlet_pressure(2.1)
            device.set_pump_status(True)
            context.state = StandbyState()
        else:
            self._timer += step


class StandbyState(State):
    def __init__(self):
        self._timer = 0

    def handle(self, context, speed_factor):
        device = context.device
        command = device.get_boiler_command()
        if command == False:
            context.state = OffState()

        current_status = device.get_device_operating_status()

        if current_status != 1:
            device.set_device_operating_status(1)
            device.set_service_mode(2)
            device.set_burner_status(False)
            print("Boiler Ready")

        supply_setpoint = device.get_supply_setpoint()
        supply_temperature = device.get_supply_temperature()
        return_temperature = device.get_return_temperature()
        stack_temperature = device.get_stack_temperature()
        air_temperature = device.get_air_temperature()
        current_inlet_pressure = device.get_inlet_pressure()
        current_outlet_pressure = device.get_outlet_pressure()

        print(f"Device on StandbyState: Supply setpoint: {supply_setpoint} Supply temperature: {supply_temperature} Return temperature: {return_temperature}")

        if (supply_setpoint*0.90) > supply_temperature:
            context.state = PurgingState()

        decrement_supply_temp = instantaneous_temperature_decrement(supply_temperature, air_temperature)
        decrement_return_temp = instantaneous_temperature_decrement(return_temperature, air_temperature)

        decrement_supply_temp *= speed_factor
        decrement_return_temp *= speed_factor

        device.set_supply_temperature(supply_temperature + decrement_supply_temp)
        device.set_return_temperature(return_temperature + decrement_return_temp)

        pressure_variation = instantaneous_pressure_variation(decrement_supply_temp)
        device.set_outlet_pressure(current_outlet_pressure + pressure_variation)
        device.set_inlet_pressure(current_inlet_pressure + pressure_variation)


        if stack_temperature > air_temperature:
            device.set_stack_temperature(stack_temperature - 2*speed_factor)

        self._timer += speed_factor

class PurgingState(State):
    def __init__(self):
        self._timer = 0 # Timer elapsed time
        self._purge_end = False
        self._purge_time = 10 # 10 Seconds durating of the purging process

    def handle(self, context, speed_factor):
        device = context.device

        command = device.get_boiler_command()
        if command == False:
            context.state = OffState()

        status = device.get_device_operating_status()
        fan_speed = device.get_fan_speed()

        stack_temperature = device.get_stack_temperature()
        air_temperature = device.get_air_temperature()
        if stack_temperature > air_temperature:
            device.set_stack_temperature(stack_temperature - 5)

        # --- Ensure correct operating mode ---
        if status != 2:
            print("Starting Purging...")
            device.set_device_operating_status(2)
            device.set_service_mode(1)

        print(f"Device on PurgingState: fan speed: {fan_speed}")

        # --- Handle fan speed logic ---
        target_speed = 3000 if not self._purge_end else 1000
        speed_step = 1000 * speed_factor

        # Smoothly adjust fan speed toward target
        if (fan_speed < target_speed) and not self._purge_end:
            device.set_fan_speed(min(fan_speed + speed_step, target_speed))
        elif fan_speed > target_speed and self._purge_end:
            device.set_fan_speed(max(fan_speed - speed_step, target_speed))

        # --- Handle purging state transitions ---
        if not self._purge_end and self._timer >= self._purge_time:
            self._purge_end = True
        elif self._purge_end and fan_speed <= 1000:
            print("Purging Finished")
            context.state = BurnerState()
            return

        self._timer += speed_factor


class BurnerState(State):
    def __init__(self):
        self._timer = 0
        self._burner_start_time = 2
        self._max_stack_temperature = 120

    def handle(self, context, step):
        device = context.device
        command = device.get_boiler_command()
        status = device.get_device_operating_status()
        if command == False:
            context.state = OffState()

        if status != 3:
            print("Starting Burning...")
            device.set_device_operating_status(3)

        current_stack_temperature = device.get_stack_temperature()
        if current_stack_temperature <= self._max_stack_temperature:
            device.set_stack_temperature(current_stack_temperature + (self._max_stack_temperature/min(self._burner_start_time, self._burner_start_time)))

        print(f"Device on BurnerState")
        if self._timer > self._burner_start_time:
            print(f"Burning Finished")
            device.set_burner_status(True)
            device.increase_ignition_starts()
            context.state = HeatingState()

        else:
            self._timer += step

class HeatingState(State):
    def __init__(self):
        self._timer = 0
        self._off_set = 20
        self._end_heating = False

    def handle(self, context, speed_factor):
        device = context.device
        command = device.get_boiler_command()
        if command == False:
            context.state = OffState()
            return

        # --- Ensure heating mode ---
        if device.get_device_operating_status() != 4:
            print("Starting Heating...")
            device.set_device_operating_status(4)
            device.set_instant_power(210)

        # --- Read temperatures ---
        current_setpoint = device.get_supply_setpoint()
        air_temperature = device.get_air_temperature()
        current_supply_temperature = device.get_supply_temperature()
        current_return_temperature = device.get_return_temperature()
        current_inlet_pressure = device.get_inlet_pressure()
        current_outlet_pressure = device.get_outlet_pressure()

        print(f"Device on HeatingState: Current setpoint: {current_setpoint}, "
              f"Supply temp: {current_supply_temperature}, Return temp: {current_return_temperature}")

        # --- Compute increment ---
        temp_increment = instantaneous_temperature_increment(current_setpoint, current_supply_temperature, air_temperature, context)
        temp_increment *= speed_factor

        # --- Update supply temperature ---
        if current_supply_temperature < current_setpoint*1.05:
            device.set_supply_temperature(current_supply_temperature + temp_increment)
        elif not self._end_heating:
            self._end_heating = True
            self._timer = 0

        if (self._timer > 8 or self._end_heating) and (current_return_temperature < current_supply_temperature * 0.60):
            device.set_return_temperature(current_return_temperature + temp_increment)

        #--- Update Pressure ----
        if not self._end_heating:
            pressure_variation = instantaneous_pressure_variation(temp_increment)
            device.set_outlet_pressure(current_outlet_pressure + pressure_variation)
            device.set_inlet_pressure(current_inlet_pressure + pressure_variation)


        # --- Check for stopping heating ---
        if self._end_heating and self._timer >= self._off_set:
            device.set_fan_speed(0)
            context.state = StandbyState()

        self._timer += speed_factor


class ErrorState(State):
    def __init__(self):
        self._valve_opened = False
        self._pressure_increment = 0.0025  # pressure increase per second

    def handle(self, context, speed_factor):
        device = context.device
        target_pressure = device.get_inlet_pressure()

        command = device.get_boiler_command()
        if command == False:
            context.state = OffState()

        # Set error state on first call
        if device.get_device_operating_status() != 5:
            print("Simulating Error due to Low Pressure!..")
            device.set_device_operating_status(5)
            device.set_burner_status(False)
            device.set_pump_status(False)
            device.set_instant_power(0.05)
            device.set_error_message(2)

        if not self._valve_opened:
            print("Simulating valve opening and system pressurization...")
            self._valve_opened = True

        # Gradually increase pressure until target is reached
        current_inlet_pressure = device.get_inlet_pressure()
        current_outlet_pressure = device.get_outlet_pressure()

        if current_inlet_pressure < target_pressure:
            new_inlet_pressure = current_inlet_pressure + self._pressure_increment * speed_factor
            device.set_inlet_pressure(new_inlet_pressure)

        if current_outlet_pressure < target_pressure:
            new_outlet_pressure = current_outlet_pressure + self._pressure_increment * speed_factor
            device.set_outlet_pressure(new_outlet_pressure)

        print(f"Inlet Pressure: {device.get_inlet_pressure():.2f} bar, Outlet Pressure: {device.get_outlet_pressure():.2f} bar")

        # Once target pressure is reached, go back to StandbyState
        if device.get_inlet_pressure() >= target_pressure and device.get_outlet_pressure() >= target_pressure:
            print("Target pressure reached. Returning to StandbyState.")
            device.set_error_message(1)
            context.state = StandbyState()