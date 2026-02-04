import datetime

def process_device_update_request(data):
    """Simple logic to process a request."""
    device_id = data.device_id
    print(f"[{datetime.datetime.now()}] Received data from {device_id}: {data.dict()}")