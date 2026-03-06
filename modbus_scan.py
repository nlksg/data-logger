from pymodbus.client import ModbusSerialClient

PORT = "/dev/ttySC0"
BAUDRATE = 9600

client = ModbusSerialClient(
    port=PORT,
    baudrate=BAUDRATE,
    bytesize=8,
    parity="N",
    stopbits=1,
    timeout=0.3
)

if not client.connect():
    print("Failed to open serial port")
    exit()

print("Scanning RS485 Modbus bus...\n")

found_devices = []

for device_id in range(1, 33):

    try:
        result = client.read_holding_registers(
            address=0,
            count=1,
            device_id=device_id
        )

        if not result.isError():
            print(f"Device found at ID {device_id}")
            found_devices.append(device_id)

    except Exception:
        pass

client.close()

print("\nScan complete")

if found_devices:
    print("Active devices:", found_devices)
else:
    print("No devices found")
