import asyncio
import BAC0
from BAC0.core.devices.local.factory import analog_input, analog_output, ObjectFactory, analog_value, multistate_value, \
    binary_value, make_state_text
from bacpypes3.basetypes import BinaryPV


class BoilerBacnetDevice:
    def __init__(self, name: str, ip: str, port: int, device_id: int):
        self._name = name
        self._ip = ip
        self._port = port
        self._device_id = device_id
        self._device = None

    def _defining_objects(self):
        ObjectFactory.clear_objects()

        # ANALOG OUTPUTS
        ao = analog_output(name="Supply Setpoint", description="Water temperature setpoint",properties={"units": "degreesCelsius"}, presentValue=70)

        # ANALOG INPUTS
        analog_input(name="Supply Temp", description="Temperature of the water leaving the boiler", properties={"units": "degreesCelsius"}, presentValue=20)
        analog_input(name="Return Temp", description="Temperature of the water returning to the boiler",properties={"units": "degreesCelsius"}, presentValue=20)
        analog_input(name="Stack Temp", description="Temperature of the exhaust gases", properties={"units": "degreesCelsius"}, presentValue=25)
        analog_input(name="Air Temp", description="Ambient air temperature", properties={"units": "degreesCelsius"},presentValue=25)
        analog_input(name="Inlet Pressure", description="Pressione dell'acqua in entrata alla caldaia", properties={"units": "bars"},presentValue=2)
        analog_input(name="Outlet Pressure", description="Pressione dell'acqua in uscita dalla caldaia", properties={"units": "bars"},presentValue=1.5)

        analog_input(name="Flow Rate", description="Water flow rate", properties={"units": "litersPerMinute"}, presentValue=0)
        analog_input(name="Fan Speed", description="Fan rotational speed", properties={"units": "revolutionsPerMinute"},presentValue=0)
        analog_input(name="Boiler Instant Power", description="Boiler instantaneous power", properties={"units": "kilowatts"}, presentValue=0)

        # ANALOG VALUES
        analog_value(name="Required Pressure", description="Target pressure requested by the system",properties={"units": "bars"}, presentValue=1.2)
        analog_value(name="Power On Seconds", description="Total seconds the boiler has been powered on",properties={"units": "seconds"}, presentValue=0)
        analog_value(name="Burner On Seconds", description="Total seconds the burner has been active",properties={"units": "seconds"}, presentValue=0)
        analog_value(name="Ignition Starts", description="Total number of burner ignitions", presentValue=0)

        # BINARY VALUES
        binary_value(name="Pump", description="Pump status", presentValue=False, inactiveText="Off", activeText="On")
        binary_value(name="Burner", description="Burner status", presentValue=False, inactiveText="Off",activeText="On")
        binary_value(name="Boiler Enable", description="Boiler enable command", presentValue=True ,inactiveText="Disabled", activeText="Enabled")
        binary_value(name="Boiler Over Temp", description="Boiler over-temperature alarm", presentValue=False,inactiveText="No", activeText="Yes")

        # MULTI VALUE OBJECTS

        operation_states = make_state_text(["Standby","Purging","Igniting","Heating","Error","Initialize","Restart","Off"])
        multistate_value(
            name="Operating Status",
            description="Operational status of the boiler",
            presentValue=10,
            stateText= operation_states
        )

        error_messages = make_state_text(["None","Low Water Pressure"])
        multistate_value(
            name="Error Message",
            description="Boiler Error Message",
            presentValue=1,
            stateText=error_messages
        )

        services_states = make_state_text(["Normal Operation","Service Standby","Restart"])
        ob = multistate_value(
            name="Service Mode",
            description="Boiler service mode",
            stateText=services_states
        )
        ob.add_objects_to_application(self._device)

    async def start(self):
        self._device = BAC0.connect(
            ip=self._ip,
            port=self._port,
            deviceId=self._device_id,
            localObjName=self._name
        )
        self._defining_objects()

    def get_device_id(self):
        return self._device_id

    def get_boiler_command(self):
        value = self._device["Boiler Enable"].presentValue
        if value == BinaryPV.active:
            return True
        return False

    def set_boiler_command(self, value):
        self._device["Boiler Enable"].presentValue = value

    def get_device_operating_status(self):
        return self._device["Operating Status"].presentValue
    def set_device_operating_status(self, operating_status_id: int):
        if 0 < operating_status_id < 10:
            self._device["Operating Status"].presentValue = operating_status_id

    def get_supply_setpoint(self):
        return self._device["Supply Setpoint"].presentValue
    def set_supply_setpoint(self, temperature):
        self._device["Supply Setpoint"].presentValue = temperature

    def get_supply_temperature(self):
        return self._device["Supply Temp"].presentValue
    def set_supply_temperature(self, temperature):
        self._device["Supply Temp"].presentValue = temperature

    def get_return_temperature(self):
        return self._device["Return Temp"].presentValue
    def set_return_temperature(self, temperature):
        self._device["Return Temp"].presentValue = temperature

    def get_stack_temperature(self):
        return self._device["Stack Temp"].presentValue
    def set_stack_temperature(self, value):
        self._device["Stack Temp"].presentValue = value

    def get_air_temperature(self):
        return self._device["Air Temp"].presentValue
    def set_air_temperature(self, temperature):
        self._device["Air Temp"].presentValue = temperature

    def get_fan_speed(self):
        return self._device["Fan Speed"].presentValue
    def set_fan_speed(self, value):
        self._device["Fan Speed"].presentValue = value

    def get_inlet_pressure(self):
        return self._device["Inlet Pressure"].presentValue
    def set_inlet_pressure(self, value):
        self._device["Inlet Pressure"].presentValue = value

    def get_outlet_pressure(self):
        return self._device["Outlet Pressure"].presentValue
    def set_outlet_pressure(self, value):
        self._device["Outlet Pressure"].presentValue = value

    def get_pump_status(self):
        value = self._device["Pump"].presentValue
        if value == BinaryPV.active:
            return True
        return False
    def set_pump_status(self, value):
        self._device["Pump"].presentValue = value

    def get_burner_status(self):
        value = self._device["Burner"].presentValue
        if value == BinaryPV.active:
            return True
        return False
    def set_burner_status(self, new_status):
        self._device["Burner"].presentValue = new_status

    def get_ignition_starts(self):
        return self._device["Ignition Starts"].presentValue
    def increase_ignition_starts(self):
        self._device["Ignition Starts"].presentValue += 1

    def get_power_seconds(self):
        return self._device["Power On Seconds"].presentValue
    def increase_power_seconds(self):
        self._device["Power On Seconds"].presentValue += 1

    def get_burner_seconds(self):
        return self._device["Burner On Seconds"].presentValue
    def increase_burner_seconds(self):
        self._device["Burner On Seconds"].presentValue += 1

    def get_instant_power(self):
        return self._device["Boiler Instant Power"].presentValue
    def set_instant_power(self, value):
        self._device["Boiler Instant Power"].presentValue = value

    def get_flow_rate(self):
        return self._device["Flow Rate"].presentValue
    def set_flow_rate(self, value):
        self._device["Flow Rate"].presentValue = value

    def get_required_pressure(self):
        return self._device["Required Pressure"].presentValue
    def set_required_pressure(self, value):
        self._device["Required Pressure"].presentValue = value

    def get_service_mode(self):
        return self._device["Service Mode"].presentValue
    def set_service_mode(self, value):
        self._device["Service Mode"].presentValue = value

    def get_error_message(self):
        return self._device["Error Message"].presentValue
    def set_error_message(self, value):
        self._device["Error Message"].presentValue = value

    async def stop(self):
        if self._device:
            self._device.disconnect()
            self._device = None
