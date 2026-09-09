import os, sys
print("=" * 50)
print("  IoT Irrigation System - Verification")
print("=" * 50)

# Check packages
ok = True
packages = ['serial', 'requests', 'dotenv']
for p in packages:
    try:
        __import__(p)
        print(f"  [OK] {p}")
    except ImportError:
        print(f"  [FAIL] {p} - run: pip install -r requirements.txt")
        ok = False

# Check .env
if os.path.exists(".env"):
    with open(".env") as f:
        content = f.read()
    if "YOUR_DEVICE_AUTH_TOKEN_HERE" in content:
        print("  [!!] .env - TOKEN NOT SET - edit .env")
        ok = False
    else:
        print("  [OK] .env - token configured")
else:
    print("  [FAIL] .env missing - copy .env.example to .env")
    ok = False

# Check COM ports
try:
    import serial.tools.list_ports
    ports = [p.device for p in serial.tools.list_ports.comports()]
    print(f"  [INFO] COM ports: {ports}")
    if "COM5" in ports and "COM6" in ports:
        print("  [OK] COM5/COM6 virtual pair ready")
    else:
        print("  [!!] COM5/COM6 not found - install com0com and run setup_com_ports.ps1")
except:
    print("  [!!] Cannot list COM ports")

# Check HEX
hexPath = r"IoT_IRRIGATION_MONITORING_SYSTEM\build\arduino.avr.uno\IoT_IRRIGATION_MONITORING_SYSTEM.ino.hex"
if os.path.exists(hexPath):
    size = os.path.getsize(hexPath)
    print(f"  [OK] HEX file compiled ({size} bytes)")
else:
    print("  [!!] HEX not found - compile in Arduino IDE")

print()
if ok:
    print("All checks passed! Ready to run: python blynk_bridge.py")
else:
    print("Fix the issues above before running.")
print("=" * 50)
