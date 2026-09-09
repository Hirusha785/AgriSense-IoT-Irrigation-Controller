# IoT Irrigation Monitoring & Controller — Blynk Cloud Edition

## Architecture Overview

```
Proteus Simulation
  └── Arduino UNO (ATMEGA328P)
        │  Hardware UART (D0/D1) @ 9600 8N1
        ▼
      COMPIM  ←── Proteus virtual serial port component
        │  COM5 (Proteus side)
        ▼
  Virtual COM Port Pair  (e.g. COM5 ↔ COM6)
        │  COM6 (Python side)
        ▼
  blynk_bridge.py  (Python 3)
        │  HTTPS
        ▼
  blynk.cloud  →  Blynk App / Web Dashboard
```

> **Local fail-safe**: If Python stops, Blynk goes offline, or Internet drops,
> the Arduino continues operating in AUTO mode independently.

---

## Files

| File | Purpose |
|------|---------|
| `IoT_IRRIGATION_MONITORING_SYSTEM.ino` | Updated Arduino firmware |
| `blynk_bridge.py` | Python cloud bridge |
| `requirements.txt` | Python dependencies |
| `.env.example` | Config template |
| `README.md` | This document |

---

## Step 1 — Proteus Modifications

### 1a. Remove Virtual Terminal
- Open the Proteus project.
- Right-click the VTERM component → Delete.
- Delete any wires connected to it on D0/D1.

### 1b. Add COMPIM
1. Press P in Proteus → search COMPIM.
2. Place it on the schematic.
3. Wire it:
   - Arduino D1 (PD1/TXD) → COMPIM RXD
   - COMPIM TXD → Arduino D0 (PD0/RXD)
4. Right-click COMPIM → Edit Properties:
   - Physical Port: COM5 (Proteus side)
   - Baud Rate: 9600
   - Data Bits: 8
   - Parity: None
   - Stop Bits: 1
   - Flow Control: None

### 1c. Add Manual Buttons (A2 and A4)
Two missing manual control buttons must be added:
- A2 Pump Button: SPST → Arduino PC2 (A2) to GND
- A4 Fan Button: SPST → Arduino PC4 (A4) to GND
No external resistor needed (INPUT_PULLUP used in code).
The existing A1 (Mode) button keeps its external pull-up resistor.

### 1d. Update HEX File Path
- Click Arduino UNO → Edit Properties → Program File.
- Set to: IoT_IRRIGATION_MONITORING_SYSTEM\build\arduino.avr.uno\IoT_IRRIGATION_MONITORING_SYSTEM.ino.hex
- Rebuild in Arduino IDE first.

---

## Step 2 — Virtual COM Port Pair (Windows)

Install com0com: https://sourceforge.net/projects/com0com/
Create pair: COM5 (Proteus) <-> COM6 (Python)
Update COMPIM property and .env SERIAL_PORT accordingly.

---

## Step 3 — Blynk Setup

1. Create account at https://blynk.cloud
2. Create Template: Name=IoT Irrigation, Hardware=Other
3. Create Device from template
4. Copy Auth Token to .env

---

## Blynk Datastreams

| Pin | Name | Type | Min | Max | Unit |
|-----|------|------|-----|-----|------|
| V0 | Temperature | Double | -10 | 80 | C |
| V1 | Humidity | Double | 0 | 100 | % |
| V2 | Soil Moisture | Integer | 0 | 100 | % |
| V3 | Pump State | Integer | 0 | 1 | |
| V4 | Fan State | Integer | 0 | 1 | |
| V5 | Current Mode | Integer | 0 | 1 | |
| V6 | Manual Pump Cmd | Integer | 0 | 1 | |
| V7 | Manual Fan Cmd | Integer | 0 | 1 | |
| V8 | Mode Command | Integer | 0 | 1 | |
| V9 | Soil Voltage | Double | 0 | 5 | V |
| V10 | Soil Raw ADC | Integer | 0 | 1023 | |

---

## Blynk Dashboard Widgets

| Widget | Type | Pin | Notes |
|--------|------|-----|-------|
| Temperature | Gauge | V0 | 0-60C |
| Humidity | Gauge | V1 | 0-100% |
| Soil Moisture | Gauge | V2 | 0-100% |
| Pump Status | LED | V3 | Green=ON |
| Fan Status | LED | V4 | Blue=ON |
| Current Mode | Value Display | V5 | 0=MANUAL 1=AUTO |
| Manual Pump | Switch | V6 | MANUAL mode only |
| Manual Fan | Switch | V7 | MANUAL mode only |
| AUTO/MANUAL | Switch | V8 | 0=MANUAL 1=AUTO |

---

## Step 4 — Python Bridge

```
pip install -r requirements.txt
copy .env.example .env
# Edit .env with your token and COM port
python blynk_bridge.py
```

---

## Serial Protocol

Arduino -> Python (every 10 s):
{"temp":31.0,"hum":89.0,"soil":70,"raw":716,"v":3.50,"pump":0,"fan":0,"mode":1}

Python -> Arduino (commands):
MODE:AUTO
MODE:MANUAL
PUMP:ON  (MANUAL mode only)
PUMP:OFF (MANUAL mode only)
FAN:ON   (MANUAL mode only)
FAN:OFF  (MANUAL mode only)

---

## Test Plan

| Test | Temp | Soil | Mode | Expected |
|------|------|------|------|---------|
| T1 | 30C | 20% | AUTO | Pump=ON, Fan=OFF |
| T2 | 37C | 80% | AUTO | Pump=OFF, Fan=ON |
| T3 | 37C | 20% | AUTO | Pump=ON, Fan=ON |
| T4 | 30C | 80% | AUTO | Pump=OFF, Fan=OFF |
| T5 | any | any | MANUAL | A2=Pump toggle, A4=Fan toggle |
| T6 | Blynk V8=0 | V6=1, V7=1 | -> MANUAL | Pump ON, Fan ON |
| T7 | Blynk V8=1 | | -> AUTO | Sensors take control |
| T8 | Internet down | | AUTO | Arduino continues |
| T9 | Python stopped | | AUTO | Arduino continues |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Cannot open COM6 | Start com0com, check Device Manager |
| No Blynk data | Check BLYNK_AUTH_TOKEN in .env |
| HTTP 400 from Blynk | Delete and recreate device, get new token |
| Arduino not responding | Rebuild HEX, update PROGRAM= path in Proteus |
| Pump/Fan ignore commands | Must be in MANUAL mode first |
| DHT shows ERROR | Wait 2-3s after Proteus start for DHT warm-up |

---

## Migrating to Real ESP8266

1. Remove COMPIM from schematic
2. Connect real ESP8266 to D2/D3 (SoftwareSerial already defined)
3. Add Blynk Arduino library: BlynkSimpleEsp8266.h
4. Replace JSON telemetry with Blynk.virtualWrite() calls
5. Replace command parsing with BLYNK_WRITE(Vx) handlers
6. Sensor and control logic needs ZERO changes
