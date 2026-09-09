"""
============================================================
  IOT IRRIGATION MONITORING & CONTROLLER SYSTEM
  Blynk Cloud Python Bridge + Local Dashboard Server
============================================================

Architecture:
  Proteus Arduino UNO
        |  COMPIM (COM5 in Proteus)
        v
  Virtual Serial Port Pair  (e.g. COM5 <-> COM6)
        |  COM6 (this script)
        v
  Python Bridge  (this script)
        |  HTTPS               |  WebSocket (ws://localhost:8765)
        v                      v
  Blynk.Cloud              Local Web Dashboard (http://localhost:8080)

Usage:
  1. Copy .env.example -> .env and fill in your values.
  2. Install: pip install -r requirements.txt
  3. Run:     python blynk_bridge.py
  4. Open:    http://localhost:8080 in your browser

Virtual Pins:
  V0  Temperature (Double, C)
  V1  Humidity    (Double, %)
  V2  Soil %      (Integer)
  V3  Pump state  (0=OFF, 1=ON)
  V4  Fan state   (0=OFF, 1=ON)
  V5  Mode        (0=MANUAL, 1=AUTO)
  V6  Manual Pump cmd  (0/1) -- Blynk switch -> Arduino
  V7  Manual Fan cmd   (0/1) -- Blynk switch -> Arduino
  V8  Mode cmd         (0=MANUAL / 1=AUTO) -- Blynk switch -> Arduino
  V9  Soil voltage     (Double, V)
  V10 Soil raw ADC     (Integer)
============================================================
"""

import os
import sys
import json
import time
import logging
import serial
import requests
import asyncio
import threading
import queue
import pathlib
import functools
import http.server

from dotenv import load_dotenv

# Optional: websockets for local dashboard
try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False

# ============================================================
# LOAD CONFIG
# ============================================================

load_dotenv()

BLYNK_SERVER   = os.getenv("BLYNK_SERVER",     "blynk.cloud")
BLYNK_TOKEN    = os.getenv("BLYNK_AUTH_TOKEN",  "")
SERIAL_PORT    = os.getenv("SERIAL_PORT",        "COM6")
BAUD_RATE      = int(os.getenv("BAUD_RATE",      "9600"))
POLL_INTERVAL  = float(os.getenv("POLL_INTERVAL", "2"))

# Dashboard server ports
WS_PORT   = int(os.getenv("WS_PORT",   "8765"))
HTTP_PORT = int(os.getenv("HTTP_PORT",  "8080"))

# Path to dashboard/ folder (relative to this script)
DASHBOARD_DIR = str(pathlib.Path(__file__).parent / "dashboard")

if not BLYNK_TOKEN or BLYNK_TOKEN == "YOUR_DEVICE_AUTH_TOKEN_HERE":
    print("WARNING: BLYNK_AUTH_TOKEN not set in .env — Blynk cloud sync disabled")
    BLYNK_ENABLED = False
else:
    BLYNK_ENABLED = True

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# Never log the token
def _safe_token():
    return BLYNK_TOKEN[:6] + "..." if len(BLYNK_TOKEN) > 6 else "***"

# ============================================================
# BLYNK HTTP API
# ============================================================

BASE_URL = f"https://{BLYNK_SERVER}"
TIMEOUT  = (5, 5)   # (connect, read) seconds

session = requests.Session()
session.headers.update({"Content-Type": "application/json"})


def blynk_update(pin: str, value) -> bool:
    """
    PUT a single value to a Blynk datastream virtual pin.
    Returns True on success.
    """
    if not BLYNK_ENABLED:
        return False
    url = f"{BASE_URL}/external/api/update?token={BLYNK_TOKEN}&{pin}={value}"
    try:
        r = session.get(url, timeout=TIMEOUT)
        if r.status_code == 200:
            return True
        log.warning("Blynk update %s=%s -> HTTP %s", pin, value, r.status_code)
        return False
    except requests.RequestException as exc:
        log.warning("Blynk update %s failed: %s", pin, exc)
        return False


def blynk_get(pin: str):
    """
    GET the current value of a Blynk virtual pin.
    Returns a string value or None on error.
    """
    if not BLYNK_ENABLED:
        return None
    url = f"{BASE_URL}/external/api/get?token={BLYNK_TOKEN}&{pin}"
    try:
        r = session.get(url, timeout=TIMEOUT)
        if r.status_code == 200:
            # Blynk returns a JSON array e.g. ["1"]
            data = r.json()
            if isinstance(data, list) and data:
                return data[0]
            return str(data)
        log.warning("Blynk get %s -> HTTP %s", pin, r.status_code)
        return None
    except requests.RequestException as exc:
        log.warning("Blynk get %s failed: %s", pin, exc)
        return None


def push_telemetry(data: dict):
    """Push all sensor readings to Blynk datastreams."""
    temp = data.get("temp")
    hum  = data.get("hum")

    if temp is not None:
        blynk_update("V0", round(float(temp), 1))
    if hum is not None:
        blynk_update("V1", round(float(hum), 1))

    blynk_update("V2",  data.get("soil",   0))
    blynk_update("V3",  data.get("pump",   0))
    blynk_update("V4",  data.get("fan",    0))
    blynk_update("V5",  data.get("mode",   1))
    blynk_update("V9",  round(float(data.get("v", 0.0)), 2))
    blynk_update("V10", data.get("raw",    0))


# ============================================================
# LOCAL DASHBOARD — WEBSOCKET SERVER
# ============================================================

# Thread-safe set of connected WebSocket clients
ws_clients = set()
ws_lock = threading.Lock()

# Asyncio event loop for the WebSocket thread
ws_loop = None

# Command queue: dashboard -> serial (thread-safe)
cmd_queue = queue.Queue()


async def ws_handler(websocket, *args):
    """Handle a single WebSocket client connection (dashboard browser)."""
    with ws_lock:
        ws_clients.add(websocket)
    client_count = len(ws_clients)
    log.info("Dashboard client connected (%d total)", client_count)

    try:
        async for raw_message in websocket:
            try:
                msg = json.loads(raw_message)
                msg_type = msg.get("type", "")

                if msg_type == "command":
                    cmd = msg.get("cmd", "").strip()
                    if cmd:
                        cmd_queue.put(cmd)
                        log.info("Dashboard -> CMD: %s", cmd)

                        # Also broadcast the command acknowledgement
                        ack = json.dumps({"type": "cmd_ack", "cmd": cmd})
                        await websocket.send(ack)

            except json.JSONDecodeError:
                log.warning("Dashboard sent invalid JSON")
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as exc:
        log.warning("WebSocket handler error: %s", exc)
    finally:
        with ws_lock:
            ws_clients.discard(websocket)
        log.info("Dashboard client disconnected (%d remaining)", len(ws_clients))


def broadcast_to_dashboard(data: dict):
    """
    Broadcast telemetry data to ALL connected dashboard clients.
    Called from the main (serial) thread — schedules onto the WS event loop.
    """
    if not ws_clients or ws_loop is None:
        return

    message = json.dumps({"type": "telemetry", "data": data})

    # Schedule the broadcast on the WebSocket event loop (thread-safe)
    asyncio.run_coroutine_threadsafe(_do_broadcast(message), ws_loop)


async def _do_broadcast(message: str):
    """Send a message to all connected WebSocket clients."""
    with ws_lock:
        clients = ws_clients.copy()

    for client in clients:
        try:
            await client.send(message)
        except Exception:
            # Client will be cleaned up by the handler's finally block
            pass


def _run_websocket_server():
    """
    Run the WebSocket server in its own asyncio event loop (background thread).
    Compatible with websockets v12+ and v15+.
    """
    global ws_loop
    ws_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(ws_loop)

    async def _serve_forever():
        async with websockets.serve(ws_handler, "0.0.0.0", WS_PORT):
            log.info("WebSocket server running on ws://0.0.0.0:%d", WS_PORT)
            await asyncio.Future()  # run forever

    ws_loop.run_until_complete(_serve_forever())


# ============================================================
# LOCAL DASHBOARD — HTTP SERVER  (serves dashboard/index.html)
# ============================================================

class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that serves dashboard files without logging every request."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DASHBOARD_DIR, **kwargs)

    def log_message(self, format, *args):
        # Suppress per-request log noise
        pass


def _run_http_server():
    """
    Serve the dashboard/ directory over HTTP (background thread).
    """
    try:
        httpd = http.server.HTTPServer(("0.0.0.0", HTTP_PORT), QuietHTTPHandler)
        log.info("Dashboard HTTP server: http://localhost:%d", HTTP_PORT)
        httpd.serve_forever()
    except OSError as exc:
        log.error("Cannot start HTTP server on port %d: %s", HTTP_PORT, exc)


# ============================================================
# SERIAL PORT MANAGEMENT
# ============================================================

def open_serial(port: str, baud: int, retries: int = 5):
    """Open serial port with retries. Returns None if unsuccessful."""
    for attempt in range(1, retries + 1):
        try:
            s = serial.Serial(
                port=port,
                baudrate=baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,
                write_timeout=2.0
            )
            log.info("Opened serial port %s @ %d baud", port, baud)
            return s
        except serial.SerialException as exc:
            log.warning("Serial open attempt %d/%d failed: %s", attempt, retries, exc)
            time.sleep(2)
    log.error("Cannot open %s after %d attempts. Is the virtual COM pair running?", port, retries)
    return None


def send_command(ser, cmd: str):
    """Send a command string to Arduino. Commands are newline terminated."""
    if ser is None:
        log.warning("Serial not connected — cannot send: %s", cmd)
        return
    try:
        ser.write((cmd + "\n").encode("ascii"))
        log.info("-> Arduino: %s", cmd)
    except serial.SerialException as exc:
        log.warning("Serial write failed: %s", exc)


# ============================================================
# COMMAND SYNCHRONIZATION
# (Track last sent values to avoid command loops)
# ============================================================

last_sent = {
    "mode": None,    # "AUTO" | "MANUAL"
    "pump": None,    # "ON"   | "OFF"
    "fan":  None,    # "ON"   | "OFF"
}

# Shadow of what Arduino last reported
arduino_state = {
    "mode": None,
    "pump": None,
    "fan":  None,
}


def sync_blynk_commands(ser: serial.Serial):
    """
    Poll Blynk V6, V7, V8 and send commands to Arduino
    only when a change is needed. PUMP/FAN commands are
    only sent when Arduino is in MANUAL mode.
    """
    # V8 = mode command (0=MANUAL, 1=AUTO)
    v8 = blynk_get("V8")
    if v8 is not None:
        desired_mode = "AUTO" if str(v8).strip() == "1" else "MANUAL"
        if desired_mode != last_sent["mode"]:
            send_command(ser, f"MODE:{desired_mode}")
            last_sent["mode"] = desired_mode

    # Only send pump/fan commands when MANUAL mode is active
    if arduino_state.get("mode") == 0:   # 0 = MANUAL

        # V6 = manual pump command
        v6 = blynk_get("V6")
        if v6 is not None:
            desired = "ON" if str(v6).strip() == "1" else "OFF"
            if desired != last_sent["pump"]:
                send_command(ser, f"PUMP:{desired}")
                last_sent["pump"] = desired

        # V7 = manual fan command
        v7 = blynk_get("V7")
        if v7 is not None:
            desired = "ON" if str(v7).strip() == "1" else "OFF"
            if desired != last_sent["fan"]:
                send_command(ser, f"FAN:{desired}")
                last_sent["fan"] = desired

    else:
        # In AUTO mode: reset last_sent so next MANUAL entry
        # picks up the current Blynk switch state properly.
        last_sent["pump"] = None
        last_sent["fan"]  = None


# ============================================================
# JSON VALIDATION
# ============================================================

EXPECTED_KEYS = {"temp", "hum", "soil", "raw", "v", "pump", "fan", "mode"}


def validate(data: dict) -> dict:
    """Clamp/validate values from Arduino JSON."""
    clean = {}

    # Temperature: None if null, else clamp 0-80
    t = data.get("temp")
    clean["temp"] = None if t is None else max(0.0, min(80.0, float(t)))

    # Humidity: None if null, else clamp 0-100
    h = data.get("hum")
    clean["hum"] = None if h is None else max(0.0, min(100.0, float(h)))

    # Soil %: 0-100
    clean["soil"] = max(0, min(100, int(data.get("soil", 0))))

    # Raw ADC: 0-1023
    clean["raw"]  = max(0, min(1023, int(data.get("raw", 0))))

    # Voltage: 0-5 V
    v = data.get("v", 0.0)
    clean["v"] = max(0.0, min(5.0, float(v)))

    # Binary states
    clean["pump"] = 1 if int(data.get("pump", 0)) else 0
    clean["fan"]  = 1 if int(data.get("fan",  0)) else 0
    clean["mode"] = 1 if int(data.get("mode", 1)) else 0

    return clean


# ============================================================
# MAIN BRIDGE LOOP
# ============================================================

def main():
    log.info("==============================================")
    log.info("  IoT Irrigation Blynk Bridge Starting")
    log.info("==============================================")
    log.info("Blynk server : %s", BLYNK_SERVER)
    log.info("Blynk token  : %s", _safe_token() if BLYNK_ENABLED else "NOT SET (cloud disabled)")
    log.info("Serial port  : %s @ %d", SERIAL_PORT, BAUD_RATE)
    log.info("Poll interval: %.1f s", POLL_INTERVAL)

    # ----------------------------------------------------------
    # Start local dashboard servers (WebSocket + HTTP)
    # ----------------------------------------------------------
    if HAS_WEBSOCKETS:
        ws_thread = threading.Thread(target=_run_websocket_server, daemon=True)
        ws_thread.start()

        http_thread = threading.Thread(target=_run_http_server, daemon=True)
        http_thread.start()

        log.info("==============================================")
        log.info("  Dashboard: http://localhost:%d", HTTP_PORT)
        log.info("  WebSocket: ws://localhost:%d", WS_PORT)
        log.info("==============================================")
    else:
        log.warning("websockets not installed — local dashboard disabled")
        log.warning("Install it with: pip install websockets")

    # ----------------------------------------------------------
    # Open serial port to Arduino (via virtual COM pair)
    # ----------------------------------------------------------
    ser = open_serial(SERIAL_PORT, BAUD_RATE)

    if ser is None:
        log.warning("======================================================")
        log.warning("  Running in DASHBOARD-ONLY mode (no serial)")
        log.warning("  Dashboard is live at http://localhost:%d", HTTP_PORT)
        log.warning("  Start Proteus + com0com, then restart this script")
        log.warning("  for full Arduino connectivity.")
        log.warning("======================================================")
        # Keep running so HTTP + WebSocket servers stay alive
        try:
            while True:
                # Process dashboard commands (queue them, but nothing to send to)
                while not cmd_queue.empty():
                    try:
                        cmd = cmd_queue.get_nowait()
                        log.info("Dashboard CMD (no serial): %s", cmd)
                    except queue.Empty:
                        break
                time.sleep(0.5)
        except KeyboardInterrupt:
            log.info("Bridge stopped by user.")
        return

    line_buf = ""
    last_poll_time = time.time()
    last_good_json = {}

    while True:
        # ------------------------------------------------
        # 1. Read incoming bytes from Arduino (non-blocking)
        # ------------------------------------------------
        try:
            waiting = ser.in_waiting
        except serial.SerialException as exc:
            log.error("Serial error: %s -- reconnecting in 5 s", exc)
            ser.close()
            time.sleep(5)
            ser = open_serial(SERIAL_PORT, BAUD_RATE)
            if ser is None:
                log.error("Reconnect failed. Exiting.")
                return
            continue

        if waiting:
            try:
                chunk = ser.read(waiting).decode("ascii", errors="replace")
            except serial.SerialException as exc:
                log.warning("Serial read error: %s", exc)
                chunk = ""

            line_buf += chunk

            # Process complete lines
            while "\n" in line_buf:
                line, line_buf = line_buf.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                log.debug("<- Arduino raw: %s", line)

                # Try to parse JSON
                if line.startswith("{"):
                    try:
                        raw_data = json.loads(line)
                        data = validate(raw_data)
                        last_good_json = data

                        # Update Arduino state shadow
                        arduino_state["mode"] = data["mode"]
                        arduino_state["pump"] = data["pump"]
                        arduino_state["fan"]  = data["fan"]

                        log.info(
                            "<- T=%.1f H=%.1f Soil=%d%% Pump=%s Fan=%s Mode=%s",
                            data["temp"] if data["temp"] is not None else float("nan"),
                            data["hum"]  if data["hum"]  is not None else float("nan"),
                            data["soil"],
                            "ON"     if data["pump"] else "OFF",
                            "ON"     if data["fan"]  else "OFF",
                            "AUTO"   if data["mode"] else "MANUAL"
                        )

                        # Push to Blynk Cloud
                        push_telemetry(data)

                        # Push to local dashboard via WebSocket
                        broadcast_to_dashboard(data)

                    except (json.JSONDecodeError, ValueError, KeyError) as exc:
                        log.warning("Malformed JSON [%s]: %s", exc, line[:60])
                else:
                    # Non-JSON line (boot messages, debug text) – log only
                    log.debug("<- (text) %s", line)

        # ------------------------------------------------
        # 2. Process commands from local dashboard
        # ------------------------------------------------
        while not cmd_queue.empty():
            try:
                cmd = cmd_queue.get_nowait()
                if cmd:
                    send_command(ser, cmd)
            except queue.Empty:
                break

        # ------------------------------------------------
        # 3. Poll Blynk for commands  (every POLL_INTERVAL)
        # ------------------------------------------------
        now = time.time()
        if now - last_poll_time >= POLL_INTERVAL:
            last_poll_time = now
            try:
                sync_blynk_commands(ser)
            except Exception as exc:
                log.warning("Blynk poll error: %s", exc)

        # Yield CPU
        time.sleep(0.05)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Bridge stopped by user.")
