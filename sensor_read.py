from pymodbus.client import ModbusSerialClient
import os
import requests
import time
from datetime import datetime, timezone

# Sensor configuration
PORT = "/dev/ttySC0"
BAUDRATE = 9600
DEVICE_ID = 1
API_URL = os.getenv("IOT_API_URL", "https://iot.myanmarapps.com/api/v1/readings/")
API_TOKEN = os.getenv("IOT_API_TOKEN", "fee259fe83bb0d58eae2fc90f11af9e7")
POLL_SECONDS = float(os.getenv("POLL_SECONDS", "2"))
DEBUG = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes", "on")

client = ModbusSerialClient(
    port=PORT,
    baudrate=BAUDRATE,
    bytesize=8,
    parity='N',
    stopbits=1,
    timeout=1
)

if not client.connect():
    print("Unable to connect to sensor")
    exit()

print("Connected to sensor")


def debug_log(message: str) -> None:
    if DEBUG:
        print(f"[DEBUG] {message}")


def send_reading(humidity: float, temperature: float) -> requests.Response:
    payload = {
        "device_id": str(DEVICE_ID),
        "humidity": humidity,
        "temperature": temperature,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    headers = {"Content-Type": "application/json"}
    if API_TOKEN:
        headers["X-API-Token"] = API_TOKEN

    debug_log(f"POST {API_URL} payload={payload}")
    response = requests.post(API_URL, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    return response

try:
    while True:

        result = client.read_holding_registers(
            address=0,
            count=2,
            device_id=DEVICE_ID
        )

        if result.isError():
            print("Read error")
        else:
            humidity_raw = result.registers[0]
            temperature_raw = result.registers[1]

            humidity = humidity_raw / 10.0
            temperature = temperature_raw / 10.0

            # handle negative temperature (two's complement)
            if temperature_raw > 32767:
                temperature = (temperature_raw - 65536) / 10.0

            print(f"Humidity: {humidity:.1f} %RH")
            print(f"Temperature: {temperature:.1f} °C")
            try:
                response = send_reading(humidity, temperature)
                debug_log(f"API success status={response.status_code} body={response.text}")
            except Exception as send_error:
                debug_log(f"API failed error={send_error}")
            print("-----")

        time.sleep(POLL_SECONDS)

except KeyboardInterrupt:
    print("Stopping")

finally:
    client.close()
