# Crestron Home REST API Technical Reference

**The Crestron Home REST API provides synchronous control over home automation devices through HTTPS endpoints at `https://{host}/cws/api`.** The API uses token-based authentication with a 10-minute session timeout, supports JSON request/response formats, and enables both individual and batch device operations. All control systems use self-signed certificates, and the CWS server initializes automatically when Crestron Home completes startup.

## Authentication architecture and token management

The authentication flow requires a two-step process starting with token generation in the Crestron Home mobile app and ending with session key retrieval.

**Initial token generation** happens within the Crestron Home app: navigate to Installer Settings → System Control Options → Web API Settings → Update Token. This generates a permanent authorization token that you copy to your clipboard for API use.

**Login endpoint** (`GET /cws/api/login`) exchanges your authorization token for a session key. Include the authorization token in a custom header:

```json
{
  "Name": "Crestron-RestAPI-AuthToken",
  "Value": "[Your Authorization Token]"
}
```

The response provides your session authentication key:

```json
{
  "version": "2.0",
  "AuthKey": "[Session Authentication Key]"
}
```

**Session management** enforces a 10-minute idle timeout per authentication key. When your key expires, the API returns HTTP 401 (Unauthorized) or 511 (Network Authentication Required). All subsequent requests require this authentication key in a custom header:

```json
{
  "Name": "Crestron-RestAPI-AuthKey",
  "Value": "[Session Authentication Key]"
}
```

**Protocol differences** between system generations: Current generation systems (CP4-R V2, MC4-R, PC4-R) use HTTPS exclusively, while older systems (PYNG-HUB, CP3-R, CP4-R V1) use HTTP. All requests and responses use `application/json` content type.

## Complete endpoint reference and HTTP methods

The API supports **GET** for retrieving data and **POST** for modifying device states. All endpoints follow a consistent pattern with base URI `https://{host}/cws/api`.

### Rooms endpoint structure

**GET /cws/api/rooms** retrieves all rooms in the system with no parameters required:

```json
{
  "rooms": [
    {
      "id": 1001,
      "name": "Whole House"
    },
    {
      "id": 1,
      "name": "Atrium"
    },
    {
      "id": 2,
      "name": "Master Room"
    }
  ],
  "version": "[API version]"
}
```

**GET /cws/api/rooms/{id}** retrieves a specific room by its unique identifier, returning the same structure filtered to that room.

### Devices discovery and capabilities

**GET /cws/api/devices** provides comprehensive device discovery, returning all devices with their type, subtype, and room assignment:

```json
{
  "devices": [
    {
      "id": 3,
      "name": "Light1",
      "type": "light",
      "subType": "Dimmer",
      "roomId": 1
    },
    {
      "id": 10,
      "name": "Shade",
      "type": "shade",
      "subType": "Shade",
      "roomId": 1
    },
    {
      "id": 13,
      "name": "TSTAT",
      "type": "thermostat",
      "roomId": 5
    }
  ],
  "version": "[API Version]"
}
```

**Device type taxonomy** includes: `light` (subtypes: Dimmer, Switch), `shade` (subtypes: Shade, Drape), `thermostat`, `lock`, `sensor` (subtypes: OccupancySensor, PhotoSensor, DoorSensor), `security Device`, and `media Zone` (subtype: Audio).

**GET /cws/api/devices/{id}** retrieves individual device details using the device's unique identifier.

### Lights control and brightness

Lights appear in the `/devices` endpoint with type "light" and subtypes "Dimmer" or "Switch". While individual light control endpoints weren't explicitly documented, light devices include these fields:

- **level**: Integer (0-65535) representing brightness, where 0 is off and 65535 is maximum brightness
- **name**: Lighting load name
- **subType**: "Dimmer" for dimmable lights, "Switch" for on/off only
- **id**: Unique lighting load identifier
- **roomId**: Room containing the light

Control operations likely follow the same pattern as other device types, though specific `/lights/SetState` endpoints weren't documented.

### Shades and blinds position control

**GET /cws/api/shades** retrieves all shades with current position and connection status:

```json
{
  "shades": [
    {
      "position": 0,
      "id": 1184,
      "name": "Midbot",
      "subType": "Shade",
      "connectionStatus": "online",
      "roomId": 1093
    }
  ],
  "version": "[API Version]"
}
```

**GET /cws/api/shades/{id}** retrieves individual shade status.

**POST /cws/api/shades/SetState** controls one or multiple shade positions simultaneously:

```json
{
  "shades": [
    {
      "id": 1,
      "position": 0
    },
    {
      "id": 2,
      "position": 65535
    }
  ]
}
```

**Position values** range from 0 (fully closed) to 65535 (fully open), providing 16-bit precision for shade positioning. The API supports batch operations and returns detailed status responses:

- **Success**: `{"status": "success", "version": "1.000.0001"}`
- **Partial success**: Includes `errorDevices` array with failed device IDs
- **Failure**: Lists all failed device IDs with error message

### Scenes activation and management

**GET /cws/api/scenes** retrieves all scenes with their current status and type classification:

```json
{
  "scenes": [
    {
      "id": 1,
      "name": "All On",
      "type": "Lighting",
      "status": false,
      "roomId": 1001
    },
    {
      "id": 9,
      "name": "MasterShade",
      "type": "Shade",
      "status": false,
      "roomId": 2
    }
  ],
  "version": "[API version]"
}
```

**Scene types** include: Lighting, Shade, Media, Climate, Lock, Shade Group, I/O, Daylight, Generic I/O, and None.

**GET /cws/api/scenes/{id}** retrieves individual scene details.

**POST /cws/api/scenes/recall/{id}** activates a specific scene by its ID, returning operation status.

### Thermostats and climate control

**GET /cws/api/thermostats** provides comprehensive thermostat information including current temperature, setpoints, modes, and available controls:

```json
{
  "thermostats": [
    {
      "mode": "Cool",
      "setPoint": {
        "type": "Cool",
        "temperature": 770,
        "minValue": 590,
        "maxValue": 990
      },
      "currentTemperature": 760,
      "temperatureUnits": "FahrenheitWholeDegrees",
      "currentFanMode": "Auto",
      "schedulerState": "run",
      "availableFanModes": ["Auto", "On"],
      "availableSystemModes": ["Off", "Cool", "Heat"],
      "availableSetPoints": [
        {
          "type": "Heat",
          "minValue": 380,
          "maxValue": 890
        },
        {
          "type": "Cool",
          "minValue": 590,
          "maxValue": 990
        }
      ],
      "id": 15,
      "name": "CTSTAT",
      "roomId": 1
    }
  ],
  "version": "[API version]"
}
```

**Temperature units** include: FahrenheitWholeDegrees, CelsiusWholeDegrees, and CelsiusHalfDegrees. Temperature values are integers representing the unit specified.

**POST /cws/api/thermostats/SetPoint** changes temperature setpoints for one or multiple thermostats:

```json
{
  "id": 15,
  "setpoints": [
    {
      "type": "Cool",
      "temperature": 750
    },
    {
      "type": "Heat",
      "temperature": 680
    }
  ]
}
```

Setpoint types include Auto, Cool, and Heat.

**POST /cws/api/thermostats/mode** changes operating modes with batch support:

```json
{
  "thermostats": [
    {
      "id": 15,
      "mode": "COOL"
    },
    {
      "id": 13,
      "mode": "HEAT"
    }
  ]
}
```

Available modes: HEAT, COOL, AUTO, OFF.

**POST /cws/api/thermostats/fanmode** controls fan operation:

```json
{
  "thermostats": [
    {
      "id": 15,
      "mode": "AUTO"
    }
  ]
}
```

Available fan modes: AUTO, ON.

**POST /cws/api/thermostats/schedule** manages schedule state:

```json
{
  "thermostats": [
    {
      "id": 15,
      "mode": "RUN"
    },
    {
      "id": 13,
      "mode": "HOLD"
    }
  ]
}
```

Available schedule modes: RUN, HOLD, OFF.

### Sensors and status monitoring

**GET /cws/api/sensors** retrieves all sensors with their current readings:

```json
{
  "sensors": [
    {
      "presence": "Unavailable",
      "id": 7,
      "name": "GLS-OIR-sensor",
      "subType": "OccupancySensor",
      "roomId": 2
    },
    {
      "level": 0,
      "id": 11,
      "name": "Photosensor",
      "subType": "PhotoSensor",
      "connectionStatus": "online",
      "roomId": 5
    }
  ],
  "version": "[API version]"
}
```

**Sensor capabilities by subtype**:

- **OccupancySensor**: Reports presence values (occupied, vacant, unavailable)
- **PhotoSensor**: Reports light level as integer value
- **DoorSensor**: Reports door status (open, closed) and battery level (Normal, Low)

**GET /cws/api/sensors/{id}** retrieves individual sensor status:

```json
{
  "sensors": [
    {
      "door status": "Closed",
      "battery level": "Normal",
      "id": 55,
      "name": "D",
      "subType": "DoorSensor",
      "roomId": 52
    }
  ],
  "version": "[API version]"
}
```

Sensors are read-only devices with no control endpoints.

### Door locks access control

Door locks appear in the `/devices` endpoint with type "lock". Specific control endpoints weren't explicitly documented, but lock devices include:

- **status**: Lock state (locked, unlocked)
- **name**: Door lock name
- **id**: Unique door lock identifier
- **roomId**: Room containing the lock

Control operations likely follow POST patterns similar to other device types.

### Media rooms and audio/video control

Media rooms appear in `/devices` with type "media Zone" and subtype "Audio". While specific control endpoints weren't documented, media room devices include:

- **currentVolumeLevel**: Current volume level (integer)
- **currentSourceId**: Active source identifier
- **currentMuteState**: Mute state (muted, unmuted)
- **availablePowerStates**: Available power states array
- **currentPowerState**: Current power state (on, off)
- **availableSources**: List of available media sources
- **availableVolumeControls**: Available volume controls (discrete)
- **name**: Media room name
- **id**: Unique media room identifier
- **roomId**: Room ID operating as media room

### Security devices and alarm systems

Security devices appear in `/devices` with type "security Device" and include:

- **availableStates**: Available states array (alarm, arm away, arm instant, arm stay, disarmed, entry delay, exit delay, fire)
- **currentState**: Current state (alarm, arm away, arm instant, arm stay, disarmed, entry delay, exit delay, fire, unknown)
- **name**: Security device name
- **id**: Unique security device identifier
- **roomId**: Room containing the device

## Device capability discovery workflow

**Implementing discovery** follows a four-step pattern: authenticate, enumerate rooms, discover devices, and parse capabilities from device metadata.

1. **Authenticate** via `/login` endpoint to obtain session key
2. **Get all rooms** via `/rooms` endpoint to understand spatial organization
3. **Get all devices** via `/devices` endpoint for complete inventory
4. **Parse device types** using `type` and `subType` fields to determine capabilities

The `type` field determines the primary device category, while `subType` provides specific implementation details. For example, type "light" with subType "Dimmer" indicates a dimmable light supporting level control (0-65535), while subType "Switch" indicates binary on/off only.

**Capability inference** happens through the `availableX` fields in device responses. Thermostats include `availableSystemModes`, `availableFanModes`, and `availableSetPoints` arrays that define valid control parameters. Media rooms include `availableSources` and `availablePowerStates` arrays.

## Error handling and response codes

**HTTP status codes** follow standard patterns:

- **200**: Success
- **401**: Unauthorized (invalid or expired authentication key)
- **511**: Network Authentication Required

**Structured error responses** provide detailed failure information:

```json
{
  "status": "failure",
  "errorMessage": "Thermostat with Id [id] has not found in the system.",
  "version": "1.000.0001"
}
```

**Error source codes** identify failure origins:

- **5001**: Session expired
- **5002**: Authentication
- **6001**: Rooms
- **7000**: Unhandled error
- **7001**: Login
- **7003**: Lights
- **7004**: Shades
- **7005**: Logout
- **7006**: Scenes
- **7007**: Thermostats
- **7008**: Fan mode
- **7009**: System mode
- **8000**: Invalid data
- **8001**: Devices
- **8005**: Security devices
- **8006**: Sensors
- **8007**: Door locks
- **8008**: Scheduler
- **8009**: Setpoint
- **8010**: Media rooms

**Partial success handling** occurs when batch operations partially fail. The response includes status "partial", an error message, and an `errorDevices` array listing failed device IDs:

```json
{
  "status": "partial",
  "errorMessage": "Shade(s) with below Id(s) are failed to update.",
  "errorDevices": [1, 2],
  "version": "1.000.0001"
}
```

## Limitations and undocumented features

**Missing control endpoints** for lights, locks, and media rooms weren't explicitly documented. These device types appear in the `/devices` discovery endpoint with their capabilities, but specific POST endpoints for control operations weren't found.

**Camera API** endpoints don't exist in the Crestron Home REST API documentation. PTZ control, streaming, and camera management may require separate APIs or third-party integrations.

**WebSocket and event subscriptions** weren't documented for Crestron Home REST API. The API operates synchronously without explicit push notification or event streaming capabilities. Real-time updates would require polling device endpoints.

**Rate limiting policies** weren't explicitly defined beyond the 10-minute authentication timeout. No documented request rate limits, throttling policies, or quota systems exist.

**API versioning strategy** isn't explicit. Version numbers appear in responses as integers or formatted strings like "1.000.0001", but no version path parameters exist in endpoints.

## Implementation example for MCP server

A complete device control flow demonstrates authentication, discovery, and control:

```javascript
// Step 1: Authenticate
const authToken = "[Token from Crestron Home App]";
const loginResponse = await fetch("https://192.168.1.100/cws/api/login", {
  method: "GET",
  headers: {
    "Crestron-RestAPI-AuthToken": authToken
  }
});
const { AuthKey } = await loginResponse.json();

// Step 2: Discover all devices
const devicesResponse = await fetch("https://192.168.1.100/cws/api/devices", {
  method: "GET",
  headers: {
    "Crestron-RestAPI-AuthKey": AuthKey
  }
});
const { devices } = await devicesResponse.json();

// Step 3: Filter by device type
const shades = devices.filter(d => d.type === "shade");
const thermostats = devices.filter(d => d.type === "thermostat");

// Step 4: Control devices (batch operation example)
const controlResponse = await fetch("https://192.168.1.100/cws/api/shades/SetState", {
  method: "POST",
  headers: {
    "Crestron-RestAPI-AuthKey": AuthKey,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    shades: [
      { id: shades[0].id, position: 32768 },  // 50% open
      { id: shades[1].id, position: 0 }       // Closed
    ]
  })
});
```

**Certificate handling** requires accepting self-signed certificates. Control systems generate 30-year certificates that renew on every restart. Your MCP server must either accept self-signed certificates or implement certificate pinning for security.

**Session refresh strategy** should monitor for 401/511 responses and automatically re-authenticate. Implement a token refresh mechanism before the 10-minute timeout expires for uninterrupted operation.

## Conclusion

The Crestron Home REST API provides comprehensive device control through a straightforward synchronous REST interface. The authentication model uses simple token-based sessions, device discovery happens through unified endpoints, and specialized control endpoints handle device-specific operations. Batch operations support efficient multi-device control, and detailed error responses enable robust error handling.

For MCP server implementation, the primary workflow involves token authentication, device discovery via `/devices`, capability parsing from device metadata, and control operations through type-specific endpoints. The API's consistency across device types simplifies implementation, though missing documentation for lights, locks, and media room control endpoints requires inference from device metadata or experimentation. Real-time device status monitoring requires polling due to absent WebSocket/event streaming capabilities.