"""
Mock Crestron Home API Server

Simulates a Crestron Home system with a typical Italian home setup.
Runs on HTTP port 8080 for testing the Crestron MCP server.

Usage:
    python mock_crestron_server.py

Then configure your MCP to use: http://localhost:8080
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, parse_qs
import threading
import sys

# ============================================================================
# Mock Data - Casa Italiana Tipica
# ============================================================================

# Session management
SESSIONS: Dict[str, Dict[str, Any]] = {}
AUTH_TOKEN = "test-token-123"

# Rooms - Stanze tipiche di una casa italiana
ROOMS = [
    {"id": 1001, "name": "Tutta la Casa"},
    {"id": 1, "name": "Soggiorno"},
    {"id": 2, "name": "Camera da Letto"},
    {"id": 3, "name": "Cucina"}
]

# Devices - Dispositivi realistici
DEVICES = [
    # Soggiorno - Luci
    {
        "id": 10,
        "name": "Lampadario Soggiorno",
        "type": "light",
        "subType": "Dimmer",
        "roomId": 1,
        "level": 65535,  # Max brightness
        "state": "on"
    },
    {
        "id": 11,
        "name": "Applique Parete",
        "type": "light",
        "subType": "Dimmer",
        "roomId": 1,
        "level": 32768,  # 50% brightness
        "state": "on"
    },
    {
        "id": 12,
        "name": "Lampada Lettura",
        "type": "light",
        "subType": "Switch",
        "roomId": 1,
        "level": 65535,
        "state": "on"
    },
    # Soggiorno - Tapparelle
    {
        "id": 20,
        "name": "Tapparella Grande",
        "type": "shade",
        "subType": "Shade",
        "roomId": 1,
        "position": 0,  # Closed
        "connectionStatus": "online"
    },
    {
        "id": 21,
        "name": "Tapparella Finestra",
        "type": "shade",
        "subType": "Shade",
        "roomId": 1,
        "position": 32768,  # 50% open
        "connectionStatus": "online"
    },
    
    # Camera da Letto - Luci
    {
        "id": 30,
        "name": "Lampadario Camera",
        "type": "light",
        "subType": "Dimmer",
        "roomId": 2,
        "level": 0,  # Off
        "state": "off"
    },
    {
        "id": 31,
        "name": "Abat-jour Sinistra",
        "type": "light",
        "subType": "Dimmer",
        "roomId": 2,
        "level": 16384,  # 25% brightness
        "state": "on"
    },
    {
        "id": 32,
        "name": "Abat-jour Destra",
        "type": "light",
        "subType": "Dimmer",
        "roomId": 2,
        "level": 16384,  # 25% brightness
        "state": "on"
    },
    # Camera da Letto - Tapparelle
    {
        "id": 40,
        "name": "Tapparella Camera",
        "type": "shade",
        "subType": "Shade",
        "roomId": 2,
        "position": 65535,  # Fully open
        "connectionStatus": "online"
    },
    # Camera da Letto - Sensori
    {
        "id": 50,
        "name": "Sensore Presenza Camera",
        "type": "sensor",
        "subType": "OccupancySensor",
        "roomId": 2,
        "presence": "occupied"
    },
    
    # Cucina - Luci
    {
        "id": 60,
        "name": "Luci Cucina",
        "type": "light",
        "subType": "Dimmer",
        "roomId": 3,
        "level": 49152,  # 75% brightness
        "state": "on"
    },
    {
        "id": 61,
        "name": "Luce Piano Lavoro",
        "type": "light",
        "subType": "Dimmer",
        "roomId": 3,
        "level": 65535,  # Max brightness
        "state": "on"
    },
    # Cucina - Sensori
    {
        "id": 70,
        "name": "Sensore Luce Finestra",
        "type": "sensor",
        "subType": "PhotoSensor",
        "roomId": 3,
        "level": 450,
        "connectionStatus": "online"
    },
    {
        "id": 71,
        "name": "Sensore Porta",
        "type": "sensor",
        "subType": "DoorSensor",
        "roomId": 3,
        "door status": "Closed",
        "battery level": "Normal"
    },
    
    # Termostato - Tutta la casa
    {
        "id": 80,
        "name": "Termostato Principale",
        "type": "thermostat",
        "subType": None,
        "roomId": 1001,
        "mode": "Cool",
        "setPoint": {
            "type": "Cool",
            "temperature": 220,  # 22°C
            "minValue": 180,
            "maxValue": 300
        },
        "currentTemperature": 235,  # 23.5°C
        "temperatureUnits": "CelsiusHalfDegrees",
        "currentFanMode": "Auto",
        "schedulerState": "run",
        "availableFanModes": ["Auto", "On"],
        "availableSystemModes": ["Off", "Cool", "Heat", "Auto"],
        "availableSetPoints": [
            {"type": "Heat", "minValue": 150, "maxValue": 250},
            {"type": "Cool", "minValue": 180, "maxValue": 300}
        ]
    }
]

# Scenes - Scene tipiche
SCENES = [
    {
        "id": 1,
        "name": "Tutto Acceso",
        "type": "Lighting",
        "status": False,
        "roomId": 1001
    },
    {
        "id": 2,
        "name": "Tutto Spento",
        "type": "Lighting",
        "status": False,
        "roomId": 1001
    },
    {
        "id": 3,
        "name": "Film",
        "type": "Lighting",
        "status": False,
        "roomId": 1
    },
    {
        "id": 4,
        "name": "Cena",
        "type": "Lighting",
        "status": False,
        "roomId": 3
    },
    {
        "id": 5,
        "name": "Notte",
        "type": "Lighting",
        "status": False,
        "roomId": 2
    },
    {
        "id": 6,
        "name": "Buongiorno",
        "type": "Shade",
        "status": False,
        "roomId": 1001
    },
    {
        "id": 7,
        "name": "Buonanotte",
        "type": "Shade",
        "status": False,
        "roomId": 1001
    }
]

# ============================================================================
# Helper Functions
# ============================================================================

def generate_session_key() -> str:
    """Generate a mock session key."""
    return f"session-{int(time.time())}-{threading.get_ident()}"


def validate_session(auth_key: str) -> bool:
    """Validate session key."""
    if auth_key not in SESSIONS:
        return False
    
    session = SESSIONS[auth_key]
    elapsed = time.time() - session["created_at"]
    
    # 10-minute timeout
    if elapsed > 600:
        del SESSIONS[auth_key]
        return False
    
    return True


def get_device_by_id(device_id: int) -> Optional[Dict[str, Any]]:
    """Get device by ID."""
    for device in DEVICES:
        if device["id"] == device_id:
            return device
    return None


def get_scene_by_id(scene_id: int) -> Optional[Dict[str, Any]]:
    """Get scene by ID."""
    for scene in SCENES:
        if scene["id"] == scene_id:
            return scene
    return None


# ============================================================================
# HTTP Request Handler
# ============================================================================

class CrestronMockHandler(BaseHTTPRequestHandler):
    """Handle HTTP requests for mock Crestron API."""
    
    def log_message(self, format, *args):
        """Custom logging."""
        print(f"[MOCK CRESTRON] {self.command} {args[0]} - {args[1]}")
    
    def _set_headers(self, status_code: int = 200):
        """Set response headers."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
    
    def _send_json(self, data: Dict[str, Any], status_code: int = 200):
        """Send JSON response."""
        self._set_headers(status_code)
        response = json.dumps(data, indent=2)
        self.wfile.write(response.encode())
    
    def _get_auth_key(self) -> Optional[str]:
        """Extract auth key from headers."""
        return self.headers.get('Crestron-RestAPI-AuthKey')
    
    def _require_auth(self) -> bool:
        """Check authentication."""
        auth_key = self._get_auth_key()
        
        if not auth_key or not validate_session(auth_key):
            self._send_json({
                "error": "Unauthorized",
                "message": "Invalid or expired session. Please authenticate again."
            }, 401)
            return False
        
        return True
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Login endpoint
        if path == "/cws/api/login":
            auth_token = self.headers.get('Crestron-RestAPI-AuthToken')
            
            if auth_token == AUTH_TOKEN:
                session_key = generate_session_key()
                SESSIONS[session_key] = {
                    "created_at": time.time()
                }
                
                print(f"✅ [AUTH] New session created: {session_key}")
                self._send_json({
                    "version": "2.0",
                    "AuthKey": session_key
                })
            else:
                print(f"❌ [AUTH] Invalid token: {auth_token}")
                self._send_json({
                    "error": "Invalid authorization token"
                }, 401)
            return
        
        # Require authentication for other endpoints
        if not self._require_auth():
            return
        
        # Rooms
        if path == "/cws/api/rooms":
            print("📋 [ROOMS] Listing all rooms")
            self._send_json({
                "rooms": ROOMS,
                "version": "2.0"
            })
            return
        
        # Devices
        if path == "/cws/api/devices":
            print("📋 [DEVICES] Listing all devices")
            self._send_json({
                "devices": DEVICES,
                "version": "2.0"
            })
            return
        
        # Shades
        if path == "/cws/api/shades":
            shades = [d for d in DEVICES if d["type"] == "shade"]
            print(f"📋 [SHADES] Listing {len(shades)} shades")
            self._send_json({
                "shades": shades,
                "version": "2.0"
            })
            return
        
        # Single shade
        if path.startswith("/cws/api/shades/") and path.count("/") == 4:
            shade_id = int(path.split("/")[-1])
            shade = get_device_by_id(shade_id)
            
            if shade and shade["type"] == "shade":
                print(f"📋 [SHADE] Getting shade {shade_id}")
                self._send_json({
                    "shades": [shade],
                    "version": "2.0"
                })
            else:
                print(f"❌ [SHADE] Shade {shade_id} not found")
                self._send_json({
                    "error": f"Shade with ID {shade_id} not found"
                }, 404)
            return
        
        # Scenes
        if path == "/cws/api/scenes":
            print(f"📋 [SCENES] Listing {len(SCENES)} scenes")
            self._send_json({
                "scenes": SCENES,
                "version": "2.0"
            })
            return
        
        # Thermostats
        if path == "/cws/api/thermostats":
            thermostats = [d for d in DEVICES if d["type"] == "thermostat"]
            print(f"📋 [THERMOSTATS] Listing {len(thermostats)} thermostats")
            self._send_json({
                "thermostats": thermostats,
                "version": "2.0"
            })
            return
        
        # Sensors
        if path == "/cws/api/sensors":
            sensors = [d for d in DEVICES if d["type"] == "sensor"]
            print(f"📋 [SENSORS] Listing {len(sensors)} sensors")
            self._send_json({
                "sensors": sensors,
                "version": "2.0"
            })
            return
        
        # Single sensor
        if path.startswith("/cws/api/sensors/") and path.count("/") == 4:
            sensor_id = int(path.split("/")[-1])
            sensor = get_device_by_id(sensor_id)
            
            if sensor and sensor["type"] == "sensor":
                print(f"📋 [SENSOR] Getting sensor {sensor_id}")
                self._send_json({
                    "sensors": [sensor],
                    "version": "2.0"
                })
            else:
                print(f"❌ [SENSOR] Sensor {sensor_id} not found")
                self._send_json({
                    "error": f"Sensor with ID {sensor_id} not found"
                }, 404)
            return
        
        # Unknown endpoint
        print(f"❌ [UNKNOWN] Unknown GET endpoint: {path}")
        self._send_json({
            "error": "Endpoint not found"
        }, 404)
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Require authentication
        if not self._require_auth():
            return
        
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else "{}"
        
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, 400)
            return
        
        # Set shade state
        if path == "/cws/api/shades/SetState":
            shades = data.get("shades", [])
            print(f"🎛️  [SHADES] Setting state for {len(shades)} shades")
            
            success_ids = []
            failed_ids = []
            
            for shade_cmd in shades:
                shade_id = shade_cmd.get("id")
                position = shade_cmd.get("position")
                
                shade = get_device_by_id(shade_id)
                
                if shade and shade["type"] == "shade":
                    shade["position"] = position
                    success_ids.append(shade_id)
                    percentage = int(position * 100 / 65535)
                    print(f"   ✅ Shade {shade_id} ({shade['name']}) → {percentage}%")
                else:
                    failed_ids.append(shade_id)
                    print(f"   ❌ Shade {shade_id} not found")
            
            if failed_ids:
                self._send_json({
                    "status": "partial" if success_ids else "failure",
                    "errorMessage": f"Shade(s) with ID(s) {failed_ids} failed to update.",
                    "errorDevices": failed_ids,
                    "version": "1.000.0001"
                })
            else:
                self._send_json({
                    "status": "success",
                    "version": "1.000.0001"
                })
            return
        
        # Recall scene
        if path.startswith("/cws/api/scenes/recall/"):
            scene_id = int(path.split("/")[-1])
            scene = get_scene_by_id(scene_id)
            
            if scene:
                # Toggle scene status
                scene["status"] = not scene["status"]
                print(f"🎬 [SCENE] Activated scene {scene_id} ({scene['name']})")
                
                # Simulate scene effects
                if "Film" in scene["name"]:
                    print("   📺 Dimming living room lights to 10%...")
                elif "Notte" in scene["name"]:
                    print("   🌙 Turning off all lights...")
                elif "Buongiorno" in scene["name"]:
                    print("   ☀️ Opening all shades...")
                
                self._send_json({
                    "status": "success",
                    "version": "1.000.0001"
                })
            else:
                print(f"❌ [SCENE] Scene {scene_id} not found")
                self._send_json({
                    "error": f"Scene with ID {scene_id} not found in the system."
                }, 404)
            return
        
        # Thermostat setpoint
        if path == "/cws/api/thermostats/SetPoint":
            thermostat_id = data.get("id")
            setpoints = data.get("setpoints", [])
            
            thermostat = get_device_by_id(thermostat_id)
            
            if thermostat and thermostat["type"] == "thermostat":
                print(f"🌡️  [THERMOSTAT] Setting {len(setpoints)} setpoint(s) for {thermostat_id}")
                
                for sp in setpoints:
                    sp_type = sp.get("type")
                    temperature = sp.get("temperature")
                    print(f"   ✅ {sp_type} setpoint → {temperature/10}°C")
                    
                    if sp_type == thermostat["setPoint"]["type"]:
                        thermostat["setPoint"]["temperature"] = temperature
                
                self._send_json({
                    "status": "success",
                    "version": "1.000.0001"
                })
            else:
                print(f"❌ [THERMOSTAT] Thermostat {thermostat_id} not found")
                self._send_json({
                    "error": f"Thermostat with ID {thermostat_id} not found in the system."
                }, 404)
            return
        
        # Thermostat mode
        if path == "/cws/api/thermostats/mode":
            thermostats = data.get("thermostats", [])
            print(f"🌡️  [THERMOSTAT] Setting mode for {len(thermostats)} thermostat(s)")
            
            for tstat in thermostats:
                tstat_id = tstat.get("id")
                mode = tstat.get("mode")
                
                thermostat = get_device_by_id(tstat_id)
                if thermostat and thermostat["type"] == "thermostat":
                    thermostat["mode"] = mode
                    print(f"   ✅ Thermostat {tstat_id} mode → {mode}")
            
            self._send_json({
                "status": "success",
                "version": "1.000.0001"
            })
            return
        
        # Thermostat fan mode
        if path == "/cws/api/thermostats/fanmode":
            thermostats = data.get("thermostats", [])
            print(f"🌡️  [THERMOSTAT] Setting fan mode for {len(thermostats)} thermostat(s)")
            
            for tstat in thermostats:
                tstat_id = tstat.get("id")
                mode = tstat.get("mode")
                
                thermostat = get_device_by_id(tstat_id)
                if thermostat and thermostat["type"] == "thermostat":
                    thermostat["currentFanMode"] = mode
                    print(f"   ✅ Thermostat {tstat_id} fan → {mode}")
            
            self._send_json({
                "status": "success",
                "version": "1.000.0001"
            })
            return
        
        # Unknown endpoint
        print(f"❌ [UNKNOWN] Unknown POST endpoint: {path}")
        self._send_json({
            "error": "Endpoint not found"
        }, 404)
    
    def do_OPTIONS(self):
        """Handle OPTIONS for CORS."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Crestron-RestAPI-AuthToken, Crestron-RestAPI-AuthKey')
        self.end_headers()


# ============================================================================
# Main Server
# ============================================================================

def run_server(port: int = 8080):
    """Run the mock Crestron server."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, CrestronMockHandler)
    
    print("=" * 70)
    print("🏠 MOCK CRESTRON HOME SERVER")
    print("=" * 70)
    print(f"\n✅ Server running on http://localhost:{port}")
    print(f"✅ API base URL: http://localhost:{port}/cws/api")
    print(f"\n🔑 Auth Token: {AUTH_TOKEN}")
    print("\n📊 Mock Data Loaded:")
    print(f"   - Stanze: {len(ROOMS)}")
    print(f"   - Dispositivi: {len(DEVICES)}")
    print(f"     • Luci: {len([d for d in DEVICES if d['type'] == 'light'])}")
    print(f"     • Tapparelle: {len([d for d in DEVICES if d['type'] == 'shade'])}")
    print(f"     • Sensori: {len([d for d in DEVICES if d['type'] == 'sensor'])}")
    print(f"     • Termostati: {len([d for d in DEVICES if d['type'] == 'thermostat'])}")
    print(f"   - Scene: {len(SCENES)}")
    
    print("\n📝 Configuration for MCP:")
    print(f"   CRESTRON_HOST=localhost:{port}")
    print(f"   CRESTRON_AUTH_TOKEN={AUTH_TOKEN}")
    
    print("\n🏘️  Stanze:")
    for room in ROOMS:
        if room["id"] != 1001:
            devices_in_room = [d for d in DEVICES if d.get("roomId") == room["id"]]
            print(f"   • {room['name']} (ID: {room['id']}) - {len(devices_in_room)} dispositivi")
    
    print("\n💡 Esempi di comandi da testare con Claude:")
    print("   1. 'Spegni il lampadario in soggiorno'")
    print("   2. 'Chiudi tutte le tapparelle'")
    print("   3. 'Attiva la scena Film'")
    print("   4. 'Imposta il termostato a 22 gradi'")
    print("   5. 'Mostrami i sensori in cucina'")
    
    print("\n🛑 Press Ctrl+C to stop the server")
    print("=" * 70)
    print()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down server...")
        httpd.shutdown()
        print("✅ Server stopped")


if __name__ == "__main__":
    port = 8080
    
    # Check if port is specified
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)
    
    run_server(port)
