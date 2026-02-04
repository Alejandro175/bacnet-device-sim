from pydantic import BaseModel

class ReceivedDeviceStatus(BaseModel):
    device_id: int
    timestamp: str
    operation_mode: int
    supply_temp: float
    return_temp: float
    outlet_pressure: float
    inlet_pressure: float
    instant_power: float
    pump_status: bool
    error_message: int

