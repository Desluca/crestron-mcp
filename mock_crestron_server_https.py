#!/usr/bin/env python3
"""
Mock Crestron Home Server with HTTPS support
For testing MCP client compatibility

Usage:
    python mock_crestron_server_https.py
"""

import ssl
import json
import uuid
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Mock data storage
MOCK_DATA = {
    "rooms": [
        {"id": 1, "name": "Soggiorno", "icon": "Living"},
        {"id": 2, "name": "Camera da Letto", "icon": "Bedroom"},
        {"id": 3, "name": "Cucina", "icon": "Kitchen"},
        {"id": 4, "name": "Studio", "icon": "Office"}
    ],
    "devices": [
        # Lights in Soggiorno (Room 1)
        {"id": 10, "name": "Lampadario Principale", "type": "light", "subType": "DimmableLight", "roomId": 1, "brightness": 80, "state": True},
        {"id": 11, "name": "Luce Lettura", "type": "light", "subType": "DimmableLight", "roomId": 1, "brightness": 50, "state": False},
        {"id": 12, "name": "Illuminazione Ambiente", "type": "light", "subType": "RGBLight", "roomId": 1, "brightness": 30, "state": True, "color": {"r": 255, "g": 200, "b": 100}},
        
        # Lights in Camera da Letto (Room 2)
        {"id": 13, "name": "Luce Principale", "type": "light", "subType": "DimmableLight", "roomId": 2, "brightness": 60, "state": False},
        {"id": 14, "name": "Comodino Destro", "type": "light", "subType": "DimmableLight", "roomId": 2, "brightness": 20, "state": True},
        {"id": 15, "name": "Comodino Sinistro", "type": "light", "subType": "DimmableLight", "roomId": 2, "brightness": 25, "state": True},
        
        # Lights in Cucina (Room 3)
        {"id": 16, "name": "Illuminazione Piano Lavoro", "type": "light", "subType": "DimmableLight", "roomId": 3, "brightness": 90, "state": True},
        {"id": 17, "name": "Luce Generale", "type": "light", "subType": "DimmableLight", "roomId": 3, "brightness": 70, "state": True},
        
        # Shades
        {"id": 20, "name": "Tapparella Grande", "type": "shade", "subType": "MotorizedShade", "roomId": 1, "position": 32767, "connectionStatus": "Connected"},
        {"id": 21, "name": "Tapparella Camera", "type": "shade", "subType": "MotorizedShade", "roomId": 2, "position": 45874, "connectionStatus": "Connected"},
        {"id": 22, "name": "Tapparella Cucina", "type": "shade", "subType": "MotorizedShade", "roomId": 3, "position": 19660, "connectionStatus": "Connected"},
        
        # Sensors
        {"id": 30, "name": "Sensore Movimento Soggiorno", "type": "sensor", "subType": "OccupancySensor", "roomId": 1, "presence": True, "batteryLevel": 85},
        {"id": 31, "name": "Sensore Luce Cucina", "type": "sensor", "subType": "PhotoSensor", "roomId": 3, "level": 450, "batteryLevel": 92},
        {"id": 32, "name": "Sensore Porta Ingresso", "type": "sensor", "subType": "DoorSensor", "roomId": 1, "door status": "Closed", "batteryLevel": 78},
        
        # Thermostat
        {"id": 80, "name": "Termostato Principale", "type": "thermostat", "subType": "Thermostat", "roomId": 1, 
         "currentTemperature": 225, "setPoint": {"type": "Cool", "temperature": 220}, "mode": "COOL", 
         "currentFanMode": "AUTO", "availableSystemModes": ["HEAT", "COOL", "AUTO", "OFF"], 
         "availableFanModes": ["AUTO", "ON"], "temperatureUnits": "Celsius",
         "heatSetPointRange": {"min": 50, "max": 350}, "coolSetPointRange": {"min": 50, "max": 350}}
    ],
    "scenes": [
        {"id": 1, "name": "Buongiorno", "type": "Lighting", "status": "NotActive", "roomId": 1},
        {"id": 2, "name": "Relax Serale", "type": "Lighting", "status": "NotActive", "roomId": 1},
        {"id": 3, "name": "Film", "type": "Lighting", "status": "NotActive", "roomId": 1},
        {"id": 4, "name": "Chiudi Tutto", "type": "Shade", "status": "NotActive", "roomId": None},
        {"id": 5, "name": "Apri Tutto", "type": "Shade", "status": "NotActive", "roomId": None},
        {"id": 6, "name": "Notte", "type": "Lighting", "status": "NotActive", "roomId": 2},
        {"id": 7, "name": "Cucina Lavoro", "type": "Lighting", "status": "NotActive", "roomId": 3}
    ]
}

# Auth sessions
AUTH_SESSIONS = {}
VALID_TOKEN = "test-token-123"

class CrestronHTTPSHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Custom logging format
        print(f"[MOCK CRESTRON HTTPS] {self.address_string()} {format%args}")
    
    def _send_cors_headers(self):
        """Send CORS headers."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Crestron-RestAPI-AuthToken, Crestron-RestAPI-AuthKey')
    
    def _send_json_response(self, data, status_code=200):
        """Send JSON response with proper headers."""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self._send_cors_headers()
        self.end_headers()
        
        json_data = json.dumps(data, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def _send_error_response(self, message, status_code=400):
        """Send error response."""
        error_data = {"error": message, "status": "error"}
        self._send_json_response(error_data, status_code)
    
    def _check_auth(self):
        """Check if request is authenticated."""
        auth_key = self.headers.get('Crestron-RestAPI-AuthKey')
        if not auth_key:
            return False
        
        return auth_key in AUTH_SESSIONS
    
    def _get_request_body(self):
        """Get request body as JSON."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                return json.loads(body.decode('utf-8'))
            return {}
        except:
            return {}
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        print(f"GET {path}")
        
        # Authentication endpoint
        if path == '/cws/api/login':
            auth_token = self.headers.get('Crestron-RestAPI-AuthToken')
            if auth_token == VALID_TOKEN:
                session_key = str(uuid.uuid4())
                AUTH_SESSIONS[session_key] = {
                    'created': time.time(),
                    'last_activity': time.time()
                }
                
                response = {
                    "AuthKey": session_key,
                    "status": "success",
                    "authenticated": True,
                    "session_valid_for": "10 minutes",
                    "api_version": "2.0"
                }
                self._send_json_response(response)
            else:
                self._send_error_response("Invalid auth token", 401)
            return
        
        # All other endpoints require authentication
        if not self._check_auth():
            self._send_error_response("Authentication required", 401)
            return
        
        # Rooms endpoint
        if path == '/cws/api/rooms':
            self._send_json_response({"rooms": MOCK_DATA["rooms"]})
            return
        
        # Devices endpoint
        if path == '/cws/api/devices':
            room_id = query_params.get('roomId', [None])[0]
            device_type = query_params.get('type', [None])[0]
            
            devices = MOCK_DATA["devices"]
            
            if room_id:
                try:
                    room_id = int(room_id)
                    devices = [d for d in devices if d.get("roomId") == room_id]
                except ValueError:
                    pass
            
            if device_type:
                devices = [d for d in devices if d.get("type") == device_type]
            
            self._send_json_response({"devices": devices})
            return
        
        # Shades endpoint
        if path == '/cws/api/shades':
            shades = [d for d in MOCK_DATA["devices"] if d.get("type") == "shade"]
            self._send_json_response({"shades": shades})
            return
        
        # Scenes endpoint
        if path == '/cws/api/scenes':
            room_id = query_params.get('roomId', [None])[0]
            scene_type = query_params.get('type', [None])[0]
            
            scenes = MOCK_DATA["scenes"]
            
            if room_id:
                try:
                    room_id = int(room_id)
                    scenes = [s for s in scenes if s.get("roomId") == room_id]
                except ValueError:
                    pass
            
            if scene_type:
                scenes = [s for s in scenes if s.get("type") == scene_type]
            
            self._send_json_response({"scenes": scenes})
            return
        
        # Thermostats endpoint
        if path == '/cws/api/thermostats':
            thermostats = [d for d in MOCK_DATA["devices"] if d.get("type") == "thermostat"]
            self._send_json_response({"thermostats": thermostats})
            return
        
        # Sensors endpoint
        if path == '/cws/api/sensors':
            subtype = query_params.get('subType', [None])[0]
            sensors = [d for d in MOCK_DATA["devices"] if d.get("type") == "sensor"]
            
            if subtype:
                sensors = [s for s in sensors if s.get("subType") == subtype]
            
            self._send_json_response({"sensors": sensors})
            return
        
        # 404 for unknown endpoints
        self._send_error_response("Endpoint not found", 404)
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        print(f"POST {path}")
        
        # All POST endpoints require authentication
        if not self._check_auth():
            self._send_error_response("Authentication required", 401)
            return
        
        body = self._get_request_body()
        
        # Set shade position
        if path == '/cws/api/shades/SetState':
            shades_to_update = body.get('shades', [])
            updated_count = 0
            
            for shade_cmd in shades_to_update:
                shade_id = shade_cmd.get('id')
                position = shade_cmd.get('position')
                
                # Find and update shade
                for device in MOCK_DATA["devices"]:
                    if device.get('id') == shade_id and device.get('type') == 'shade':
                        # Convert 0-100% to Crestron's 0-65535 range
                        device['position'] = int(position * 65535 / 100)
                        updated_count += 1
                        break
            
            if updated_count > 0:
                response = {"status": "success", "shades_updated": updated_count}
            else:
                response = {"status": "error", "message": "No shades updated"}
            
            self._send_json_response(response)
            return
        
        # Activate scene
        if path.startswith('/cws/api/scenes/recall/'):
            try:
                scene_id = int(path.split('/')[-1])
                
                # Find scene
                scene = None
                for s in MOCK_DATA["scenes"]:
                    if s.get('id') == scene_id:
                        scene = s
                        break
                
                if scene:
                    # Reset all scenes to NotActive
                    for s in MOCK_DATA["scenes"]:
                        s['status'] = 'NotActive'
                    
                    # Activate requested scene
                    scene['status'] = 'Active'
                    
                    response = {"status": "success", "scene_id": scene_id, "message": "Scene activated"}
                else:
                    response = {"status": "error", "message": "Scene not found"}
                
                self._send_json_response(response)
                return
            except ValueError:
                self._send_error_response("Invalid scene ID", 400)
                return
        
        # Set thermostat setpoint
        if path == '/cws/api/thermostats/SetPoint':
            thermostat_id = body.get('id')
            setpoints = body.get('setpoints', [])
            
            # Find thermostat
            thermostat = None
            for device in MOCK_DATA["devices"]:
                if device.get('id') == thermostat_id and device.get('type') == 'thermostat':
                    thermostat = device
                    break
            
            if thermostat and setpoints:
                updated_count = 0
                for setpoint in setpoints:
                    sp_type = setpoint.get('type')
                    temperature = setpoint.get('temperature')
                    
                    if sp_type and temperature is not None:
                        thermostat['setPoint'] = {
                            'type': sp_type,
                            'temperature': temperature
                        }
                        updated_count += 1
                
                if updated_count > 0:
                    response = {"status": "success", "thermostat_id": thermostat_id, "setpoints_updated": updated_count}
                else:
                    response = {"status": "error", "message": "No setpoints updated"}
            else:
                response = {"status": "error", "message": "Thermostat not found or no setpoints provided"}
            
            self._send_json_response(response)
            return
        
        # Set thermostat mode
        if path == '/cws/api/thermostats/SetMode':
            thermostats = body.get('thermostats', [])
            updated_count = 0
            
            for tstat_cmd in thermostats:
                tstat_id = tstat_cmd.get('id')
                mode = tstat_cmd.get('mode')
                
                # Find and update thermostat
                for device in MOCK_DATA["devices"]:
                    if device.get('id') == tstat_id and device.get('type') == 'thermostat':
                        if mode in device.get('availableSystemModes', []):
                            device['mode'] = mode
                            updated_count += 1
                        break
            
            if updated_count > 0:
                response = {"status": "success", "thermostats_updated": updated_count}
            else:
                response = {"status": "error", "message": "No thermostats updated"}
            
            self._send_json_response(response)
            return
        
        # Set thermostat fan mode
        if path == '/cws/api/thermostats/SetFan':
            thermostats = body.get('thermostats', [])
            updated_count = 0
            
            for tstat_cmd in thermostats:
                tstat_id = tstat_cmd.get('id')
                fan_mode = tstat_cmd.get('mode')
                
                # Find and update thermostat
                for device in MOCK_DATA["devices"]:
                    if device.get('id') == tstat_id and device.get('type') == 'thermostat':
                        if fan_mode in device.get('availableFanModes', []):
                            device['currentFanMode'] = fan_mode
                            updated_count += 1
                        break
            
            if updated_count > 0:
                response = {"status": "success", "thermostats_updated": updated_count}
            else:
                response = {"status": "error", "message": "No thermostats updated"}
            
            self._send_json_response(response)
            return
        
        # 404 for unknown endpoints
        self._send_error_response("Endpoint not found", 404)

def run_https_server():
    """Run the mock HTTPS server."""
    print("=" * 70)
    print("🏠 MOCK CRESTRON HOME SERVER (HTTPS)")
    print("=" * 70)
    
    server_address = ('localhost', 8080)
    httpd = HTTPServer(server_address, CrestronHTTPSHandler)
    
    # Create SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('server.crt', 'server.key')
    
    # Wrap the socket with SSL
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    
    print(f"✅ HTTPS Server running on https://localhost:8080")
    print(f"✅ API base URL: https://localhost:8080/cws/api")
    print(f"🔑 Auth Token: {VALID_TOKEN}")
    print("📊 Mock Data Loaded:")
    print(f"   - Stanze: {len(MOCK_DATA['rooms'])}")
    print(f"   - Dispositivi: {len(MOCK_DATA['devices'])}")
    
    devices_by_type = {}
    for device in MOCK_DATA['devices']:
        dtype = device.get('type', 'unknown')
        devices_by_type[dtype] = devices_by_type.get(dtype, 0) + 1
    
    for dtype, count in devices_by_type.items():
        print(f"     • {dtype.title()}: {count}")
    
    print(f"   - Scene: {len(MOCK_DATA['scenes'])}")
    print("📝 Configuration for MCP:")
    print("   CRESTRON_HOST=localhost:8080")
    print(f"   CRESTRON_AUTH_TOKEN={VALID_TOKEN}")
    print("🏘️  Stanze:")
    for room in MOCK_DATA['rooms']:
        room_devices = [d for d in MOCK_DATA['devices'] if d.get('roomId') == room['id']]
        print(f"   • {room['name']} (ID: {room['id']}) - {len(room_devices)} dispositivi")
    
    print("💡 Esempi di comandi da testare con Claude:")
    print("   1. 'Spegni il lampadario in soggiorno'")
    print("   2. 'Chiudi tutte le tapparelle'")
    print("   3. 'Attiva la scena Film'")
    print("   4. 'Imposta il termostato a 22 gradi'")
    print("   5. 'Mostrami i sensori in cucina'")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 70)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.server_close()

if __name__ == "__main__":
    run_https_server()
