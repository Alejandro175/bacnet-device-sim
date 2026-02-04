

**Comando di avvio**


Avvio simulazione (directory: DeviceSimulation)
```
python script.py 'YOUR_IP' 47808 --deviceID 'YOUR_DEVICE_ID' --initial_setpoint 'WANTED_SET_POINT' --simulation_mode 'SELECTED_MODE' --speed_factor 'SELECTED_SPEED'```
```

--deviceID: L’ID univoco del device BACnet simulato.

--initial_setpoint: La temperatura desiderata per il boiler, in gradi Celsius.

--simulation_mode: La modalità di simulazione; 0 per simulazione normale, 1 per simulazione con errore di pressione.

--speed_factor: Il fattore di velocità della simulazione; 1 significa tempo reale, valori più alti accelerano la simulazione.

**Comando per simulazione 1:1 secondi**
```
python script.py 192.168.1.10 47808 --deviceID 1234 --initial_setpoint 70 --simulation_mode 0 --speed_factor 1
```

**Comando per simulazione 1:10 secondi (simulazione accelerata)**
```
python script.py 192.168.1.10 47808 --deviceID 1234 --initial_setpoint 70 --simulation_mode 0 --speed_factor 10
```

**Avvio simulazione con errore di pressione**
```
python script.py 192.168.1.10 47808 --deviceID 1234 --initial_setpoint 70 --simulation_mode 1 --speed_factor 1
```

**Avvio del Web Server (directory: WebServer)**
```
python server.py
```