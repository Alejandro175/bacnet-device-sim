from fastapi import FastAPI, Depends, HTTPException, Header, Response
from controller.device_controller import process_device_update_request
from models.device import ReceivedDeviceStatus
import uvicorn

# Simulazione API KEY per la autenticazione del endpoint
API_KEY = "EXAMPLE_API_KEY"

app = FastAPI(title="Device IoT Receiver", description="Receive device updates from Bacnet API", version="1.0")

async def verify_api_key(authorization: str = Header(...)):
    if authorization != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

@app.get("/health")
async def root():
    return {"status": "ok"}

@app.post("/device/upload", dependencies=[Depends(verify_api_key)])
async def upload_device_data(data: ReceivedDeviceStatus):
    process_device_update_request(data)
    return Response(status_code=204)

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8099, reload=True)