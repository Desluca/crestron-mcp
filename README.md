# Crestron Home MCP Server

A production-ready Model Context Protocol (MCP) server for controlling Crestron Home automation systems. This server enables LLMs to discover and control Crestron devices including lights, shades, scenes, thermostats, sensors, and more through natural language.

## Features

### ✨ Comprehensive Device Control
- **Rooms & Devices**: Full discovery of rooms and all device types
- **Shades/Blinds**: Position control (0-100%), batch operations
- **Scenes**: List and activate pre-configured scenes
- **Thermostats**: Complete climate control (temperature, mode, fan, schedule)
- **Sensors**: Read occupancy, light, door, and battery status
- **Natural Language Resolution**: Fuzzy matching for device names in any language

### 🛡️ Production-Ready Features
- **Session Management**: Automatic authentication with 10-minute session handling
- **Error Handling**: Comprehensive error messages with actionable guidance
- **Character Limits**: Smart truncation with helpful pagination guidance
- **Batch Operations**: Control multiple devices simultaneously
- **Multi-format Output**: JSON and Markdown response formats
- **SSL Support**: Handles self-signed certificates from Crestron systems

### 🌍 Multi-Language Support
- Italian: "Spegni la luce del lampadario in soggiorno"
- English: "Turn off the living room chandelier"
- Any language: Natural language device resolution with confidence scoring

## Requirements

- Python 3.10 or higher
- Crestron Home system with REST API enabled
- Network access to Crestron Home system
- Authorization token from Crestron Home app

## Installation

### 1. Clone or Download

```bash
# Download the files
# - crestron_mcp.py
# - requirements.txt
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Get Crestron Authorization Token

1. Open the **Crestron Home** mobile app
2. Navigate to: **Installer Settings** → **System Control Options** → **Web API Settings**
3. Tap **Update Token**
4. Copy the generated authorization token
5. Save it securely - you'll need it for authentication

## Usage

### Running the MCP Server

The server uses stdio transport by default, which is suitable for integration with MCP clients:

```bash
python crestron_mcp.py
```

For testing or debugging, you can run with a timeout:

```bash
timeout 5s python crestron_mcp.py
```

### Integration with Claude Desktop

Add to your Claude Desktop MCP configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "crestron": {
      "command": "python",
      "args": ["/path/to/crestron_mcp.py"]
    }
  }
}
```

## Available Tools

### 🔐 Authentication

#### `crestron_authenticate`
Establish session with Crestron Home system. **Must be called first before any other operations.**

**Parameters:**
- `host` (string): Crestron Home IP or hostname (e.g., "192.168.1.100")
- `auth_token` (string): Authorization token from Crestron Home app

**Example:**
```json
{
  "host": "192.168.1.100",
  "auth_token": "your-token-here"
}
```

### 🏠 Discovery

#### `crestron_list_rooms`
Get all rooms configured in the system.

**Parameters:**
- `response_format` (optional): "markdown" (default) or "json"

#### `crestron_list_devices`
Discover all devices with filtering options.

**Parameters:**
- `room_id` (optional): Filter by room ID
- `device_type` (optional): Filter by type (light, shade, thermostat, sensor, etc.)
- `response_format` (optional): "markdown" or "json"

### 🪟 Shade Control

#### `crestron_get_shades`
Get current shade positions and status.

**Parameters:**
- `shade_id` (optional): Specific shade ID
- `response_format` (optional): "markdown" or "json"

#### `crestron_set_shade_position`
Control shade positions (0 = closed, 100 = open).

**Parameters:**
- `shades` (array): List of shade commands with `id` and `position` (0-100)

**Example:**
```json
{
  "shades": [
    {"id": 1, "position": 50},
    {"id": 2, "position": 100}
  ]
}
```

### 🎬 Scene Control

#### `crestron_list_scenes`
List all available scenes with filters.

**Parameters:**
- `room_id` (optional): Filter by room
- `scene_type` (optional): Filter by type (Lighting, Shade, Media, Climate, etc.)
- `response_format` (optional): "markdown" or "json"

#### `crestron_activate_scene`
Activate a scene by ID.

**Parameters:**
- `scene_id` (integer): Scene ID to activate

### 🌡️ Thermostat Control

#### `crestron_get_thermostats`
Get thermostat status and capabilities.

**Parameters:**
- `thermostat_id` (optional): Specific thermostat ID
- `response_format` (optional): "markdown" or "json"

#### `crestron_set_thermostat_setpoint`
Set temperature setpoints.

**Parameters:**
- `thermostat_id` (integer): Thermostat ID
- `setpoints` (array): List of setpoint commands with `type` (Heat/Cool/Auto) and `temperature`

**Example:**
```json
{
  "thermostat_id": 15,
  "setpoints": [
    {"type": "Cool", "temperature": 72},
    {"type": "Heat", "temperature": 68}
  ]
}
```

#### `crestron_set_thermostat_mode`
Set system mode (HEAT, COOL, AUTO, OFF).

**Parameters:**
- `thermostats` (array): List of thermostat commands with `id` and `mode`

#### `crestron_set_thermostat_fan`
Set fan mode (AUTO, ON).

**Parameters:**
- `thermostats` (array): List of thermostat commands with `id` and `mode`

### 📡 Sensors

#### `crestron_get_sensors`
Get sensor readings (occupancy, light level, door status, battery).

**Parameters:**
- `sensor_id` (optional): Specific sensor ID
- `sensor_subtype` (optional): Filter by subtype (OccupancySensor, PhotoSensor, DoorSensor)
- `response_format` (optional): "markdown" or "json"

### 🔍 Device Resolution

#### `crestron_resolve_device`
Resolve natural language descriptions to specific devices using fuzzy matching.

**Parameters:**
- `utterance` (string): Natural language device description in any language
- `preferred_room_id` (optional): Room context for narrowing search

**Example:**
```json
{
  "utterance": "lampadario in soggiorno",
  "preferred_room_id": 1
}
```

**Returns:**
- High confidence (≥0.8): Single resolved device
- Low confidence (<0.8): Multiple candidates requiring clarification

## Workflow Examples

### Example 1: Italian User Command

**User**: "Spegni la luce del lampadario in soggiorno" (Turn off the living room chandelier)

**Workflow:**
1. **Authenticate**: `crestron_authenticate` with host and token
2. **Discover rooms**: `crestron_list_rooms` to find "soggiorno" room ID
3. **Resolve device**: `crestron_resolve_device` with utterance "lampadario soggiorno"
4. **Get device details**: Use returned device_id with `crestron_list_devices`
5. **Control device**: Set the light level to 0 (implementation depends on device type)

### Example 2: Set Morning Scene

**User**: "Activate the morning scene"

**Workflow:**
1. **Authenticate**: `crestron_authenticate`
2. **List scenes**: `crestron_list_scenes` to find "Morning" scene
3. **Activate**: `crestron_activate_scene` with scene_id

### Example 3: Climate Control

**User**: "Set bedroom thermostat to 72 degrees cool"

**Workflow:**
1. **Authenticate**: `crestron_authenticate`
2. **Find thermostat**: `crestron_get_thermostats` or `crestron_resolve_device`
3. **Set temperature**: `crestron_set_thermostat_setpoint` with Cool setpoint at 72
4. **Set mode**: `crestron_set_thermostat_mode` to COOL

### Example 4: Batch Shade Control

**User**: "Close all shades in the living room"

**Workflow:**
1. **Authenticate**: `crestron_authenticate`
2. **Find room**: `crestron_list_rooms` to get living room ID
3. **Find shades**: `crestron_list_devices` filtered by room_id and type "shade"
4. **Control all**: `crestron_set_shade_position` with all shade IDs at position 0

## Architecture

### Session Management
- 10-minute session timeout with 1-minute buffer
- Automatic session validation before each API call
- Clear error messages when re-authentication needed

### Error Handling
- Comprehensive HTTP error handling with status codes
- Actionable error messages guide users to solutions
- Graceful handling of authentication failures and timeouts

### Response Formats

**Markdown Format** (default):
- Human-readable with headers and formatting
- Optimized for display to users
- Includes helpful context and summaries

**JSON Format**:
- Machine-readable structured data
- Complete field inclusion for programmatic processing
- Consistent schema across all tools

### Character Limits
- 25,000 character response limit
- Smart truncation with clear indicators
- Helpful guidance on filtering and pagination

## API Reference

### Crestron Home REST API

**Base URL**: `https://{host}/cws/api`

**Authentication**:
- Header: `Crestron-RestAPI-AuthKey: {session_key}`
- Session lifetime: 10 minutes
- All systems use self-signed SSL certificates

**Supported Endpoints**:
- `/login` - Authentication
- `/rooms` - Room discovery
- `/devices` - Device discovery
- `/shades` - Shade control and status
- `/shades/SetState` - Shade position control
- `/scenes` - Scene discovery
- `/scenes/recall/{id}` - Scene activation
- `/thermostats` - Thermostat status
- `/thermostats/SetPoint` - Temperature control
- `/thermostats/mode` - System mode control
- `/thermostats/fanmode` - Fan control
- `/sensors` - Sensor readings

## Troubleshooting

### Authentication Issues

**Problem**: "Not authenticated or session expired"
**Solution**: Call `crestron_authenticate` first with valid host and token

**Problem**: "Authentication failed"
**Solutions**:
1. Verify host IP/hostname is correct and reachable
2. Regenerate token in Crestron Home app
3. Ensure Web API is enabled in Crestron Home settings
4. Check network connectivity

### SSL Certificate Warnings

**Problem**: SSL verification warnings
**Solution**: The server automatically handles self-signed certificates. This is expected behavior for Crestron systems.

### Device Not Found

**Problem**: "Device with ID X not found"
**Solution**: 
1. Use `crestron_list_devices` to see all available devices
2. Verify device ID is correct
3. Check device is online with `crestron_get_shades` or appropriate status tool

### Response Truncated

**Problem**: Large responses are truncated
**Solution**:
1. Use filtering parameters (room_id, device_type)
2. Request specific devices by ID
3. Use pagination where available
4. Choose JSON format for more compact output

## Security Considerations

### Token Storage
- Never commit authorization tokens to version control
- Store tokens securely (environment variables, secure vaults)
- Rotate tokens periodically in Crestron Home app

### Network Security
- Use VPN when accessing Crestron systems remotely
- Implement IP whitelisting on Crestron system if available
- Monitor API access logs

### Session Security
- Sessions expire after 10 minutes automatically
- Re-authenticate for each session
- Monitor for unauthorized access attempts

## Development

### Code Structure

```
crestron_mcp.py
├── Constants & Configuration
├── Enums & Models (Pydantic)
├── Session Management
├── Helper Functions
│   ├── authenticate()
│   ├── api_request()
│   ├── format_markdown_list()
│   ├── truncate_response()
│   └── format_device_markdown()
├── Tools (MCP @mcp.tool decorated)
│   ├── Authentication
│   ├── Discovery
│   ├── Shade Control
│   ├── Scene Control
│   ├── Thermostat Control
│   ├── Sensor Monitoring
│   └── Device Resolution
└── Main Entry Point
```

### Testing

**Syntax Check**:
```bash
python -m py_compile crestron_mcp.py
```

**Import Check**:
```bash
python -c "import crestron_mcp"
```

**Run Server** (will wait for MCP client connections):
```bash
python crestron_mcp.py
```

### Extending the Server

To add new device types or capabilities:

1. **Add Pydantic Models**: Define input validation models
2. **Create Tool Function**: Use `@mcp.tool` decorator
3. **Implement API Logic**: Use helper functions for API calls
4. **Add Error Handling**: Provide clear, actionable error messages
5. **Format Response**: Support both JSON and Markdown formats
6. **Update Documentation**: Add to this README

## Performance

- **Async/await**: All I/O operations are async for optimal performance
- **Connection Pooling**: Single HTTP client instance reused across requests
- **Session Caching**: Authentication key cached for session lifetime
- **Batch Operations**: Support for controlling multiple devices in single API call

## Limitations

### API Limitations
- Camera control not available in Crestron Home REST API
- Light control endpoints not explicitly documented (use device discovery)
- Door lock control endpoints not explicitly documented
- Media room control endpoints not explicitly documented
- No WebSocket/event streaming (polling required for real-time updates)

### MCP Server Limitations
- Stdio transport only (HTTP/SSE not configured)
- Single concurrent session per server instance
- No rate limiting implemented (respects Crestron system limits)

## Contributing

This is a production-ready implementation following MCP best practices. Contributions welcome for:

- Additional device type support (lights, locks, media rooms)
- Enhanced device resolution algorithms
- Rate limiting and request queuing
- WebSocket event support (if added to Crestron API)
- Additional transport options (HTTP, SSE)

## License

[Your License Here]

## Support

For issues related to:
- **MCP Server**: Review error messages and logs
- **Crestron API**: Consult Crestron Home REST API documentation
- **Device Control**: Verify device IDs and capabilities with discovery tools
- **Authentication**: Check token validity and network connectivity

## Acknowledgments

Built with:
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) - FastMCP framework
- [httpx](https://www.python-httpx.org/) - Async HTTP client
- [Pydantic](https://docs.pydantic.dev/) - Data validation

Based on the Crestron Home REST API specification and MCP best practices for building high-quality LLM integrations.
