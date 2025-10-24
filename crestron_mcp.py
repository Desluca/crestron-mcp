"""
Crestron Home MCP Server

A Model Context Protocol server for controlling Crestron Home automation systems.
Provides tools for discovering rooms, devices, and controlling lights, shades, scenes,
thermostats, sensors, and more through the Crestron Home REST API.
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
import httpx
import json
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager

# Constants
CHARACTER_LIMIT = 25000
API_TIMEOUT = 30.0
SESSION_TIMEOUT = 540  # 9 minutes (10-minute session timeout with 1-minute buffer)

# FastMCP server will be initialized after lifespan function

# ============================================================================
# Enums and Models
# ============================================================================

class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class ThermostatMode(str, Enum):
    """Available thermostat system modes."""
    HEAT = "HEAT"
    COOL = "COOL"
    AUTO = "AUTO"
    OFF = "OFF"


class FanMode(str, Enum):
    """Available thermostat fan modes."""
    AUTO = "AUTO"
    ON = "ON"


class ScheduleMode(str, Enum):
    """Available thermostat schedule modes."""
    RUN = "RUN"
    HOLD = "HOLD"
    OFF = "OFF"


class SetPointType(str, Enum):
    """Available thermostat setpoint types."""
    HEAT = "Heat"
    COOL = "Cool"
    AUTO = "Auto"


# ============================================================================
# Session Management
# ============================================================================

class CrestronSession:
    """Manages Crestron API authentication and session lifecycle."""
    
    def __init__(self):
        self.host: Optional[str] = None
        self.auth_key: Optional[str] = None
        self.session_start: Optional[float] = None
        self.client: Optional[httpx.AsyncClient] = None
        
    def is_valid(self) -> bool:
        """Check if session is still valid."""
        if not self.auth_key or not self.session_start:
            return False
        # Check if session has expired (with 1-minute buffer)
        elapsed = asyncio.get_event_loop().time() - self.session_start
        return elapsed < SESSION_TIMEOUT
    
    def clear(self):
        """Clear session data."""
        self.auth_key = None
        self.session_start = None


# Global session instance
_session = CrestronSession()


@asynccontextmanager
async def app_lifespan(app):
    """Manage HTTP client lifecycle."""
    # Initialize HTTP client with SSL verification disabled for self-signed certs
    _session.client = httpx.AsyncClient(
        verify=False,
        timeout=httpx.Timeout(API_TIMEOUT),
        follow_redirects=True
    )
    yield {"client": _session.client}
    # Cleanup
    if _session.client:
        await _session.client.aclose()


mcp = FastMCP("crestron_mcp", lifespan=app_lifespan)


# ============================================================================
# Helper Functions
# ============================================================================

async def authenticate(host: str, auth_token: str) -> Dict[str, Any]:
    """
    Authenticate with Crestron Home and obtain session key.
    
    Args:
        host: Crestron Home hostname or IP
        auth_token: Authorization token from Crestron Home app
        
    Returns:
        dict: Response containing AuthKey and version
        
    Raises:
        httpx.HTTPStatusError: On authentication failure
    """
    if not _session.client:
        raise RuntimeError("HTTP client not initialized")
        
    url = f"https://{host}/cws/api/login"
    headers = {"Crestron-RestAPI-AuthToken": auth_token}
    
    response = await _session.client.get(url, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    
    # Update global session
    _session.host = host
    _session.auth_key = data.get("AuthKey")
    _session.session_start = asyncio.get_event_loop().time()
    
    return data


async def api_request(
    endpoint: str,
    method: str = "GET",
    body: Optional[Dict[str, Any]] = None,
    require_auth: bool = True
) -> Dict[str, Any]:
    """
    Make authenticated request to Crestron API.
    
    Args:
        endpoint: API endpoint path (e.g., "/rooms", "/devices")
        method: HTTP method (GET or POST)
        body: Optional request body for POST requests
        require_auth: Whether authentication is required
        
    Returns:
        dict: API response data
        
    Raises:
        ValueError: If not authenticated when required
        httpx.HTTPStatusError: On API error
    """
    if require_auth:
        if not _session.is_valid():
            raise ValueError(
                "Not authenticated or session expired. Please authenticate first using "
                "crestron_authenticate tool."
            )
    
    if not _session.client:
        raise RuntimeError("HTTP client not initialized")
    
    url = f"https://{_session.host}/cws/api{endpoint}"
    headers = {}
    
    if require_auth and _session.auth_key:
        headers["Crestron-RestAPI-AuthKey"] = _session.auth_key
    
    if method == "GET":
        response = await _session.client.get(url, headers=headers)
    elif method == "POST":
        headers["Content-Type"] = "application/json"
        response = await _session.client.post(url, headers=headers, json=body)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")
    
    response.raise_for_status()
    return response.json()


def format_markdown_list(items: List[Dict[str, Any]], fields: List[str]) -> str:
    """Format list of items as markdown table."""
    if not items:
        return "No items found."
    
    result = []
    for item in items:
        item_lines = []
        for field in fields:
            value = item.get(field)
            if value is not None:
                item_lines.append(f"  - **{field.replace('_', ' ').title()}**: {value}")
        if item_lines:
            result.append("\n".join(item_lines))
            result.append("")
    
    return "\n".join(result)


def truncate_response(response: str, items_count: int = 0) -> str:
    """Truncate response if it exceeds character limit."""
    if len(response) <= CHARACTER_LIMIT:
        return response
    
    truncated = response[:CHARACTER_LIMIT]
    truncation_msg = (
        f"\n\n⚠️ **Response Truncated**\n"
        f"The response was truncated from {len(response):,} to {CHARACTER_LIMIT:,} characters. "
    )
    
    if items_count > 0:
        truncation_msg += (
            f"Try using filters, reducing the limit parameter, "
            f"or requesting specific items to see more details."
        )
    else:
        truncation_msg += "Try requesting specific items or using filters to reduce the response size."
    
    return truncated + truncation_msg


def format_device_markdown(device: Dict[str, Any]) -> str:
    """Format a single device as markdown."""
    lines = [f"### {device.get('name', 'Unknown')} (ID: {device.get('id')})"]
    lines.append(f"- **Type**: {device.get('type', 'Unknown')}")
    
    if 'subType' in device:
        lines.append(f"- **Subtype**: {device['subType']}")
    if 'roomId' in device:
        lines.append(f"- **Room ID**: {device['roomId']}")
    
    # Type-specific fields
    if device.get('type') == 'light':
        if 'level' in device:
            brightness = int(device['level'] * 100 / 65535)
            lines.append(f"- **Brightness**: {brightness}%")
    
    elif device.get('type') == 'shade':
        if 'position' in device:
            position = int(device['position'] * 100 / 65535)
            lines.append(f"- **Position**: {position}% open")
        if 'connectionStatus' in device:
            lines.append(f"- **Connection**: {device['connectionStatus']}")
    
    elif device.get('type') == 'thermostat':
        if 'mode' in device:
            lines.append(f"- **Mode**: {device['mode']}")
        if 'currentTemperature' in device:
            lines.append(f"- **Current Temp**: {device['currentTemperature']}°")
        if 'setPoint' in device:
            sp = device['setPoint']
            lines.append(f"- **Setpoint**: {sp.get('temperature')}° ({sp.get('type')})")
        if 'currentFanMode' in device:
            lines.append(f"- **Fan Mode**: {device['currentFanMode']}")
    
    elif device.get('type') == 'sensor':
        if 'presence' in device:
            lines.append(f"- **Presence**: {device['presence']}")
        if 'level' in device:
            lines.append(f"- **Light Level**: {device['level']}")
        if 'door status' in device:
            lines.append(f"- **Door Status**: {device['door status']}")
        if 'battery level' in device:
            lines.append(f"- **Battery**: {device['battery level']}")
    
    lines.append("")
    return "\n".join(lines)


# ============================================================================
# Authentication Tool
# ============================================================================

class AuthenticateInput(BaseModel):
    """Input for Crestron authentication."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    host: str = Field(
        ...,
        description="Crestron Home hostname or IP address (e.g., '192.168.1.100' or 'crestron.local')",
        min_length=1,
        max_length=255
    )
    auth_token: str = Field(
        ...,
        description=(
            "Authorization token from Crestron Home app. Generate in: "
            "Installer Settings → System Control Options → Web API Settings → Update Token"
        ),
        min_length=1
    )


@mcp.tool(
    name="crestron_authenticate",
    annotations={
        "title": "Authenticate with Crestron Home",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crestron_authenticate(params: AuthenticateInput) -> str:
    """
    Authenticate with Crestron Home system and establish a session.
    
    This tool must be called first before using any other Crestron tools. The session
    expires after 10 minutes of inactivity. Generate the auth token in the Crestron Home
    mobile app under: Installer Settings → System Control Options → Web API Settings → Update Token
    
    Args:
        params (AuthenticateInput): Authentication parameters containing:
            - host (str): Crestron Home hostname or IP address
            - auth_token (str): Authorization token from Crestron Home app
    
    Returns:
        str: JSON response with authentication status and session information:
            {
                "status": "success",
                "host": "192.168.1.100",
                "authenticated": true,
                "session_valid_for": "10 minutes",
                "api_version": "2.0"
            }
    """
    try:
        result = await authenticate(params.host, params.auth_token)
        
        response = {
            "status": "success",
            "host": params.host,
            "authenticated": True,
            "session_valid_for": "10 minutes",
            "api_version": result.get("version", "unknown"),
            "message": "Successfully authenticated with Crestron Home. You can now use other tools."
        }
        
        return json.dumps(response, indent=2)
        
    except httpx.HTTPStatusError as e:
        error_response = {
            "status": "error",
            "error": "Authentication failed",
            "details": str(e),
            "help": (
                "Verify that: (1) The host is correct and reachable, "
                "(2) The auth token is valid and not expired, "
                "(3) Web API is enabled in Crestron Home settings"
            )
        }
        return json.dumps(error_response, indent=2)
    except Exception as e:
        error_response = {
            "status": "error",
            "error": str(e),
            "help": "Check network connectivity and Crestron Home system status"
        }
        return json.dumps(error_response, indent=2)


# ============================================================================
# Discovery Tools
# ============================================================================

class ListRoomsInput(BaseModel):
    """Input for listing rooms."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="crestron_list_rooms",
    annotations={
        "title": "List All Rooms",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crestron_list_rooms(params: ListRoomsInput) -> str:
    """
    Retrieve all rooms configured in the Crestron Home system.
    
    Rooms are spatial groupings that contain devices. This is typically the first
    discovery step to understand the home's organization before querying devices.
    
    Args:
        params (ListRoomsInput): Input parameters containing:
            - response_format (str): Output format ('markdown' or 'json')
    
    Returns:
        str: List of rooms with their IDs and names in specified format:
            Markdown: Formatted list with room names and IDs
            JSON: Array of room objects with 'id' and 'name' fields
    """
    try:
        data = await api_request("/rooms")
        rooms = data.get("rooms", [])
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps({"rooms": rooms, "count": len(rooms)}, indent=2)
        else:
            # Markdown format
            if not rooms:
                result = "No rooms found in the Crestron Home system."
            else:
                result = f"# Rooms ({len(rooms)} total)\n\n"
                for room in rooms:
                    result += f"- **{room.get('name')}** (ID: {room.get('id')})\n"
        
        return truncate_response(result, len(rooms))
        
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to retrieve rooms",
            "details": str(e)
        }, indent=2)


class ListDevicesInput(BaseModel):
    """Input for listing devices."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    room_id: Optional[int] = Field(
        default=None,
        description="Optional room ID to filter devices by room (e.g., 1, 2, 1001)",
        ge=1
    )
    device_type: Optional[str] = Field(
        default=None,
        description=(
            "Optional device type filter. Available types: 'light', 'shade', 'thermostat', "
            "'sensor', 'lock', 'security Device', 'media Zone'"
        )
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="crestron_list_devices",
    annotations={
        "title": "List All Devices",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crestron_list_devices(params: ListDevicesInput) -> str:
    """
    Discover all devices or filter by room and/or device type.
    
    This is the primary device discovery tool. Returns comprehensive information about
    each device including its type, subtype, current state, and capabilities. Use this
    to find device IDs needed for control operations.
    
    Args:
        params (ListDevicesInput): Input parameters containing:
            - room_id (Optional[int]): Filter by room ID
            - device_type (Optional[str]): Filter by device type
            - response_format (str): Output format ('markdown' or 'json')
    
    Returns:
        str: List of devices with their properties in specified format:
            Markdown: Formatted list with device details grouped by type
            JSON: Array of device objects with all available fields
    """
    try:
        data = await api_request("/devices")
        devices = data.get("devices", [])
        
        # Apply filters
        if params.room_id is not None:
            devices = [d for d in devices if d.get("roomId") == params.room_id]
        
        if params.device_type:
            devices = [d for d in devices if d.get("type") == params.device_type]
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps({
                "devices": devices,
                "count": len(devices),
                "filters": {
                    "room_id": params.room_id,
                    "device_type": params.device_type
                }
            }, indent=2)
        else:
            # Markdown format
            if not devices:
                filter_msg = []
                if params.room_id:
                    filter_msg.append(f"room {params.room_id}")
                if params.device_type:
                    filter_msg.append(f"type '{params.device_type}'")
                filter_str = " with " + " and ".join(filter_msg) if filter_msg else ""
                result = f"No devices found{filter_str}."
            else:
                result = f"# Devices ({len(devices)} total)\n\n"
                
                # Group by type
                by_type: Dict[str, List[Dict[str, Any]]] = {}
                for device in devices:
                    dtype = device.get('type', 'unknown')
                    if dtype not in by_type:
                        by_type[dtype] = []
                    by_type[dtype].append(device)
                
                for dtype, devices_of_type in sorted(by_type.items()):
                    result += f"## {dtype.title()} ({len(devices_of_type)})\n\n"
                    for device in devices_of_type:
                        result += format_device_markdown(device)
        
        return truncate_response(result, len(devices))
        
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to retrieve devices",
            "details": str(e)
        }, indent=2)


# ============================================================================
# Shade Control Tools
# ============================================================================

class GetShadesInput(BaseModel):
    """Input for getting shade status."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    shade_id: Optional[int] = Field(
        default=None,
        description="Optional shade ID to get specific shade (e.g., 1184). Omit to get all shades.",
        ge=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="crestron_get_shades",
    annotations={
        "title": "Get Shade Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crestron_get_shades(params: GetShadesInput) -> str:
    """
    Get current status of shades/blinds including position and connection status.
    
    Returns detailed information about shades including their current position (0-100%),
    connection status, room assignment, and subtype. Position 0 = fully closed, 100 = fully open.
    
    Args:
        params (GetShadesInput): Input parameters containing:
            - shade_id (Optional[int]): Specific shade ID or None for all shades
            - response_format (str): Output format ('markdown' or 'json')
    
    Returns:
        str: Shade information in specified format:
            Markdown: Formatted list with shade details and current positions
            JSON: Array of shade objects with all fields including position, connectionStatus
    """
    try:
        endpoint = f"/shades/{params.shade_id}" if params.shade_id else "/shades"
        data = await api_request(endpoint)
        shades = data.get("shades", [])
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps({"shades": shades, "count": len(shades)}, indent=2)
        else:
            # Markdown format
            if not shades:
                result = "No shades found."
            else:
                result = f"# Shades ({len(shades)} total)\n\n"
                for shade in shades:
                    position = int(shade.get('position', 0) * 100 / 65535)
                    result += f"### {shade.get('name')} (ID: {shade.get('id')})\n"
                    result += f"- **Position**: {position}% open\n"
                    result += f"- **Connection**: {shade.get('connectionStatus', 'unknown')}\n"
                    result += f"- **Room ID**: {shade.get('roomId')}\n"
                    result += f"- **Subtype**: {shade.get('subType')}\n\n"
        
        return truncate_response(result, len(shades))
        
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to retrieve shades",
            "details": str(e)
        }, indent=2)


class ShadePosition(BaseModel):
    """Single shade position command."""
    model_config = ConfigDict(validate_assignment=True, extra='forbid')
    
    id: int = Field(..., description="Shade device ID", ge=1)
    position: int = Field(
        ...,
        description="Shade position: 0 (fully closed) to 100 (fully open)",
        ge=0,
        le=100
    )


class SetShadeStateInput(BaseModel):
    """Input for setting shade positions."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    shades: List[ShadePosition] = Field(
        ...,
        description="List of shade positions to set. Each entry contains shade ID and position (0-100)",
        min_length=1,
        max_length=50
    )


@mcp.tool(
    name="crestron_set_shade_position",
    annotations={
        "title": "Set Shade Position",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crestron_set_shade_position(params: SetShadeStateInput) -> str:
    """
    Control one or more shades/blinds by setting their position.
    
    Sets shade positions where 0 = fully closed and 100 = fully open. Supports batch
    operations to control multiple shades simultaneously. The operation is idempotent.
    
    Args:
        params (SetShadeStateInput): Input parameters containing:
            - shades (List[ShadePosition]): Array of shade commands with id and position (0-100)
    
    Returns:
        str: JSON response with operation status:
            Success: {"status": "success", "shades_updated": 2}
            Partial: {"status": "partial", "success": [1], "failed": [2], "message": "..."}
            Error: {"status": "error", "message": "..."}
    """
    try:
        # Convert percentage (0-100) to Crestron scale (0-65535)
        shades_data = []
        for shade in params.shades:
            crestron_position = int(shade.position * 65535 / 100)
            shades_data.append({
                "id": shade.id,
                "position": crestron_position
            })
        
        body = {"shades": shades_data}
        result = await api_request("/shades/SetState", method="POST", body=body)
        
        status = result.get("status", "unknown")
        response = {
            "status": status,
            "shades_updated": len(params.shades),
            "details": result
        }
        
        if status == "partial":
            response["message"] = (
                "Some shades failed to update. Check 'errorDevices' in details. "
                "Verify shade IDs are correct and devices are online."
            )
        elif status == "success":
            response["message"] = f"Successfully updated {len(params.shades)} shade(s)"
        
        return json.dumps(response, indent=2)
        
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({
            "error": "Failed to set shade positions",
            "status_code": e.response.status_code,
            "details": str(e)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to set shade positions",
            "details": str(e)
        }, indent=2)


# ============================================================================
# Scene Control Tools
# ============================================================================

class ListScenesInput(BaseModel):
    """Input for listing scenes."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    room_id: Optional[int] = Field(
        default=None,
        description="Optional room ID to filter scenes by room",
        ge=1
    )
    scene_type: Optional[str] = Field(
        default=None,
        description=(
            "Optional scene type filter. Available types: 'Lighting', 'Shade', 'Media', "
            "'Climate', 'Lock', 'Shade Group', 'I/O', 'Daylight', 'Generic I/O', 'None'"
        )
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="crestron_list_scenes",
    annotations={
        "title": "List Scenes",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crestron_list_scenes(params: ListScenesInput) -> str:
    """
    List all scenes with their current status and type.
    
    Scenes are pre-configured automation scenarios that can control multiple devices
    simultaneously. Returns scene names, IDs, types, current status, and room assignments.
    
    Args:
        params (ListScenesInput): Input parameters containing:
            - room_id (Optional[int]): Filter by room ID
            - scene_type (Optional[str]): Filter by scene type
            - response_format (str): Output format ('markdown' or 'json')
    
    Returns:
        str: List of scenes in specified format:
            Markdown: Formatted list with scene details and activation status
            JSON: Array of scene objects with id, name, type, status, roomId
    """
    try:
        data = await api_request("/scenes")
        scenes = data.get("scenes", [])
        
        # Apply filters
        if params.room_id is not None:
            scenes = [s for s in scenes if s.get("roomId") == params.room_id]
        
        if params.scene_type:
            scenes = [s for s in scenes if s.get("type") == params.scene_type]
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps({
                "scenes": scenes,
                "count": len(scenes),
                "filters": {
                    "room_id": params.room_id,
                    "scene_type": params.scene_type
                }
            }, indent=2)
        else:
            # Markdown format
            if not scenes:
                result = "No scenes found."
            else:
                result = f"# Scenes ({len(scenes)} total)\n\n"
                
                # Group by type
                by_type: Dict[str, List[Dict[str, Any]]] = {}
                for scene in scenes:
                    stype = scene.get('type', 'unknown')
                    if stype not in by_type:
                        by_type[stype] = []
                    by_type[stype].append(scene)
                
                for stype, scenes_of_type in sorted(by_type.items()):
                    result += f"## {stype} Scenes ({len(scenes_of_type)})\n\n"
                    for scene in scenes_of_type:
                        status_emoji = "✓" if scene.get('status') else "○"
                        result += f"- {status_emoji} **{scene.get('name')}** (ID: {scene.get('id')}) - Room {scene.get('roomId')}\n"
                    result += "\n"
        
        return truncate_response(result, len(scenes))
        
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to retrieve scenes",
            "details": str(e)
        }, indent=2)


class RecallSceneInput(BaseModel):
    """Input for recalling a scene."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    scene_id: int = Field(
        ...,
        description="Scene ID to activate (e.g., 1, 9, 15)",
        ge=1
    )


@mcp.tool(
    name="crestron_activate_scene",
    annotations={
        "title": "Activate Scene",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def crestron_activate_scene(params: RecallSceneInput) -> str:
    """
    Activate a scene to apply pre-configured device settings.
    
    Recalls (activates) a scene which will apply all configured device states associated
    with that scene. This can control multiple devices simultaneously (lights, shades, etc.).
    
    Args:
        params (RecallSceneInput): Input parameters containing:
            - scene_id (int): ID of the scene to activate
    
    Returns:
        str: JSON response with activation status:
            Success: {"status": "success", "scene_id": 1, "message": "Scene activated"}
            Error: {"status": "error", "message": "Scene not found"}
    """
    try:
        result = await api_request(f"/scenes/recall/{params.scene_id}", method="POST")
        
        response = {
            "status": "success",
            "scene_id": params.scene_id,
            "message": "Scene activated successfully",
            "details": result
        }
        
        return json.dumps(response, indent=2)
        
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return json.dumps({
                "error": f"Scene with ID {params.scene_id} not found",
                "help": "Use crestron_list_scenes to see available scenes"
            }, indent=2)
        return json.dumps({
            "error": "Failed to activate scene",
            "status_code": e.response.status_code,
            "details": str(e)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to activate scene",
            "details": str(e)
        }, indent=2)


# ============================================================================
# Thermostat Control Tools
# ============================================================================

class GetThermostatsInput(BaseModel):
    """Input for getting thermostat status."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    thermostat_id: Optional[int] = Field(
        default=None,
        description="Optional thermostat ID to get specific thermostat. Omit to get all thermostats.",
        ge=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="crestron_get_thermostats",
    annotations={
        "title": "Get Thermostat Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crestron_get_thermostats(params: GetThermostatsInput) -> str:
    """
    Get current status and capabilities of thermostats.
    
    Returns comprehensive thermostat information including current temperature, setpoints,
    operating mode, fan mode, temperature units, available modes, and setpoint ranges.
    
    Args:
        params (GetThermostatsInput): Input parameters containing:
            - thermostat_id (Optional[int]): Specific thermostat ID or None for all
            - response_format (str): Output format ('markdown' or 'json')
    
    Returns:
        str: Thermostat information in specified format:
            Markdown: Formatted list with current status and capabilities
            JSON: Array of thermostat objects with all fields including mode, setPoint,
                  currentTemperature, availableSystemModes, availableFanModes, etc.
    """
    try:
        data = await api_request("/thermostats")
        thermostats = data.get("thermostats", [])
        
        # Filter if specific ID requested
        if params.thermostat_id is not None:
            thermostats = [t for t in thermostats if t.get("id") == params.thermostat_id]
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps({"thermostats": thermostats, "count": len(thermostats)}, indent=2)
        else:
            # Markdown format
            if not thermostats:
                result = "No thermostats found."
            else:
                result = f"# Thermostats ({len(thermostats)} total)\n\n"
                for tstat in thermostats:
                    result += f"### {tstat.get('name')} (ID: {tstat.get('id')})\n"
                    result += f"- **Current Temperature**: {tstat.get('currentTemperature')}° {tstat.get('temperatureUnits', '')}\n"
                    result += f"- **Mode**: {tstat.get('mode')}\n"
                    result += f"- **Fan Mode**: {tstat.get('currentFanMode')}\n"
                    
                    if 'setPoint' in tstat:
                        sp = tstat['setPoint']
                        result += f"- **Setpoint**: {sp.get('temperature')}° ({sp.get('type')})\n"
                        result += f"  - Range: {sp.get('minValue')}° - {sp.get('maxValue')}°\n"
                    
                    result += f"- **Schedule**: {tstat.get('schedulerState', 'unknown')}\n"
                    
                    if 'availableSystemModes' in tstat:
                        result += f"- **Available Modes**: {', '.join(tstat['availableSystemModes'])}\n"
                    
                    result += f"- **Room ID**: {tstat.get('roomId')}\n\n"
        
        return truncate_response(result, len(thermostats))
        
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to retrieve thermostats",
            "details": str(e)
        }, indent=2)


class ThermostatSetpoint(BaseModel):
    """Single setpoint setting."""
    model_config = ConfigDict(validate_assignment=True, extra='forbid')
    
    type: SetPointType = Field(..., description="Setpoint type: 'Heat', 'Cool', or 'Auto'")
    temperature: int = Field(
        ...,
        description="Target temperature in the thermostat's configured units",
        ge=0,
        le=1000
    )


class SetThermostatSetpointInput(BaseModel):
    """Input for setting thermostat setpoints."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    thermostat_id: int = Field(
        ...,
        description="Thermostat device ID",
        ge=1
    )
    setpoints: List[ThermostatSetpoint] = Field(
        ...,
        description="List of setpoints to configure (Heat, Cool, or Auto)",
        min_length=1,
        max_length=3
    )


@mcp.tool(
    name="crestron_set_thermostat_setpoint",
    annotations={
        "title": "Set Thermostat Setpoint",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crestron_set_thermostat_setpoint(params: SetThermostatSetpointInput) -> str:
    """
    Set temperature setpoints for a thermostat.
    
    Changes the target temperature setpoints. Can set Heat, Cool, or Auto setpoints.
    Temperature values use the units configured on the thermostat (Fahrenheit or Celsius).
    Check valid ranges using crestron_get_thermostats first.
    
    Args:
        params (SetThermostatSetpointInput): Input parameters containing:
            - thermostat_id (int): ID of the thermostat
            - setpoints (List[ThermostatSetpoint]): Setpoints with type and temperature
    
    Returns:
        str: JSON response with operation status:
            Success: {"status": "success", "thermostat_id": 15, "setpoints_updated": 2}
            Error: {"status": "error", "message": "Temperature out of range"}
    """
    try:
        # Format setpoints for API
        setpoints_data = [
            {"type": sp.type.value, "temperature": sp.temperature}
            for sp in params.setpoints
        ]
        
        body = {
            "id": params.thermostat_id,
            "setpoints": setpoints_data
        }
        
        result = await api_request("/thermostats/SetPoint", method="POST", body=body)
        
        response = {
            "status": "success",
            "thermostat_id": params.thermostat_id,
            "setpoints_updated": len(params.setpoints),
            "message": f"Successfully updated {len(params.setpoints)} setpoint(s)",
            "details": result
        }
        
        return json.dumps(response, indent=2)
        
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({
            "error": "Failed to set thermostat setpoint",
            "status_code": e.response.status_code,
            "details": str(e),
            "help": "Verify temperature is within valid range for this thermostat"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to set thermostat setpoint",
            "details": str(e)
        }, indent=2)


class ThermostatModeCommand(BaseModel):
    """Single thermostat mode command."""
    model_config = ConfigDict(validate_assignment=True, extra='forbid')
    
    id: int = Field(..., description="Thermostat device ID", ge=1)
    mode: ThermostatMode = Field(..., description="System mode: HEAT, COOL, AUTO, or OFF")


class SetThermostatModeInput(BaseModel):
    """Input for setting thermostat system mode."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    thermostats: List[ThermostatModeCommand] = Field(
        ...,
        description="List of thermostats and their target modes",
        min_length=1,
        max_length=50
    )


@mcp.tool(
    name="crestron_set_thermostat_mode",
    annotations={
        "title": "Set Thermostat Mode",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crestron_set_thermostat_mode(params: SetThermostatModeInput) -> str:
    """
    Set operating mode for one or more thermostats.
    
    Changes the thermostat system mode (HEAT, COOL, AUTO, OFF). Supports batch operations.
    Available modes vary by thermostat - check with crestron_get_thermostats first.
    
    Args:
        params (SetThermostatModeInput): Input parameters containing:
            - thermostats (List[ThermostatModeCommand]): Array with id and mode for each
    
    Returns:
        str: JSON response with operation status:
            Success: {"status": "success", "thermostats_updated": 2}
            Partial: {"status": "partial", "success": [15], "failed": [13]}
            Error: {"status": "error", "message": "..."}
    """
    try:
        # Format for API
        thermostats_data = [
            {"id": t.id, "mode": t.mode.value}
            for t in params.thermostats
        ]
        
        body = {"thermostats": thermostats_data}
        result = await api_request("/thermostats/mode", method="POST", body=body)
        
        response = {
            "status": result.get("status", "success"),
            "thermostats_updated": len(params.thermostats),
            "message": f"Successfully updated {len(params.thermostats)} thermostat(s)",
            "details": result
        }
        
        return json.dumps(response, indent=2)
        
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to set thermostat mode",
            "details": str(e)
        }, indent=2)


class ThermostatFanCommand(BaseModel):
    """Single thermostat fan mode command."""
    model_config = ConfigDict(validate_assignment=True, extra='forbid')
    
    id: int = Field(..., description="Thermostat device ID", ge=1)
    mode: FanMode = Field(..., description="Fan mode: AUTO or ON")


class SetThermostatFanInput(BaseModel):
    """Input for setting thermostat fan mode."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    thermostats: List[ThermostatFanCommand] = Field(
        ...,
        description="List of thermostats and their target fan modes",
        min_length=1,
        max_length=50
    )


@mcp.tool(
    name="crestron_set_thermostat_fan",
    annotations={
        "title": "Set Thermostat Fan Mode",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crestron_set_thermostat_fan(params: SetThermostatFanInput) -> str:
    """
    Set fan mode for one or more thermostats.
    
    Controls the thermostat fan operation mode. AUTO runs fan only when heating/cooling,
    ON runs fan continuously. Supports batch operations.
    
    Args:
        params (SetThermostatFanInput): Input parameters containing:
            - thermostats (List[ThermostatFanCommand]): Array with id and mode for each
    
    Returns:
        str: JSON response with operation status:
            Success: {"status": "success", "thermostats_updated": 1}
            Error: {"status": "error", "message": "..."}
    """
    try:
        thermostats_data = [
            {"id": t.id, "mode": t.mode.value}
            for t in params.thermostats
        ]
        
        body = {"thermostats": thermostats_data}
        result = await api_request("/thermostats/fanmode", method="POST", body=body)
        
        response = {
            "status": "success",
            "thermostats_updated": len(params.thermostats),
            "message": f"Successfully updated fan mode for {len(params.thermostats)} thermostat(s)",
            "details": result
        }
        
        return json.dumps(response, indent=2)
        
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to set thermostat fan mode",
            "details": str(e)
        }, indent=2)


# ============================================================================
# Sensor Tools
# ============================================================================

class GetSensorsInput(BaseModel):
    """Input for getting sensor status."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    sensor_id: Optional[int] = Field(
        default=None,
        description="Optional sensor ID to get specific sensor. Omit to get all sensors.",
        ge=1
    )
    sensor_subtype: Optional[str] = Field(
        default=None,
        description="Optional filter by sensor subtype: 'OccupancySensor', 'PhotoSensor', 'DoorSensor'"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="crestron_get_sensors",
    annotations={
        "title": "Get Sensor Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crestron_get_sensors(params: GetSensorsInput) -> str:
    """
    Get current readings from sensors (occupancy, photo, door sensors).
    
    Returns current sensor readings including presence detection, light levels,
    door status, battery levels, and connection status. Sensors are read-only devices.
    
    Args:
        params (GetSensorsInput): Input parameters containing:
            - sensor_id (Optional[int]): Specific sensor ID or None for all
            - sensor_subtype (Optional[str]): Filter by subtype
            - response_format (str): Output format ('markdown' or 'json')
    
    Returns:
        str: Sensor readings in specified format:
            Markdown: Formatted list with current readings and status
            JSON: Array of sensor objects with readings (presence, level, door status, battery)
    """
    try:
        endpoint = f"/sensors/{params.sensor_id}" if params.sensor_id else "/sensors"
        data = await api_request(endpoint)
        sensors = data.get("sensors", [])
        
        # Apply subtype filter
        if params.sensor_subtype:
            sensors = [s for s in sensors if s.get("subType") == params.sensor_subtype]
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps({"sensors": sensors, "count": len(sensors)}, indent=2)
        else:
            # Markdown format
            if not sensors:
                result = "No sensors found."
            else:
                result = f"# Sensors ({len(sensors)} total)\n\n"
                
                # Group by subtype
                by_subtype: Dict[str, List[Dict[str, Any]]] = {}
                for sensor in sensors:
                    subtype = sensor.get('subType', 'unknown')
                    if subtype not in by_subtype:
                        by_subtype[subtype] = []
                    by_subtype[subtype].append(sensor)
                
                for subtype, sensors_of_type in sorted(by_subtype.items()):
                    result += f"## {subtype} ({len(sensors_of_type)})\n\n"
                    for sensor in sensors_of_type:
                        result += f"### {sensor.get('name')} (ID: {sensor.get('id')})\n"
                        
                        if 'presence' in sensor:
                            result += f"- **Presence**: {sensor['presence']}\n"
                        if 'level' in sensor:
                            result += f"- **Light Level**: {sensor['level']}\n"
                        if 'door status' in sensor:
                            result += f"- **Door Status**: {sensor['door status']}\n"
                        if 'battery level' in sensor:
                            result += f"- **Battery**: {sensor['battery level']}\n"
                        if 'connectionStatus' in sensor:
                            result += f"- **Connection**: {sensor['connectionStatus']}\n"
                        
                        result += f"- **Room ID**: {sensor.get('roomId')}\n\n"
        
        return truncate_response(result, len(sensors))
        
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to retrieve sensors",
            "details": str(e)
        }, indent=2)


# ============================================================================
# Device Resolution Tool (MCP Requirement)
# ============================================================================

class ResolveDeviceInput(BaseModel):
    """Input for device resolution."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    utterance: str = Field(
        ...,
        description=(
            "Natural language device description in any language (e.g., 'lampadario in soggiorno', "
            "'living room chandelier', 'bedroom lights')"
        ),
        min_length=1,
        max_length=500
    )
    preferred_room_id: Optional[int] = Field(
        default=None,
        description="Optional room ID to narrow search context",
        ge=1
    )


@mcp.tool(
    name="crestron_resolve_device",
    annotations={
        "title": "Resolve Device from Natural Language",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crestron_resolve_device(params: ResolveDeviceInput) -> str:
    """
    Resolve natural language device description to specific device(s).
    
    Uses fuzzy matching to find devices based on natural language descriptions in any
    language. Returns confidence scores and suggests alternatives if multiple matches found.
    Helps disambiguate user requests like "turn on the bedroom light" to specific device IDs.
    
    Args:
        params (ResolveDeviceInput): Input parameters containing:
            - utterance (str): Natural language description of device
            - preferred_room_id (Optional[int]): Room context for narrowing search
    
    Returns:
        str: JSON response with matched devices and confidence scores:
            High confidence (>0.8): Single device with high match score
            Low confidence (<0.8): Multiple candidates requiring clarification:
                {
                    "resolved": false,
                    "confidence": 0.6,
                    "candidates": [...],
                    "clarification_needed": true
                }
    """
    try:
        # Get all devices
        data = await api_request("/devices")
        devices = data.get("devices", [])
        
        # Also get rooms for name matching
        rooms_data = await api_request("/rooms")
        rooms = rooms_data.get("rooms", [])
        room_map = {r["id"]: r["name"].lower() for r in rooms}
        
        # Normalize utterance for matching
        utterance_lower = params.utterance.lower()
        
        # Scoring function
        matches = []
        for device in devices:
            score = 0.0
            device_name = device.get("name", "").lower()
            device_type = device.get("type", "").lower()
            device_room_id = device.get("roomId")
            
            # Exact name match
            if device_name in utterance_lower or utterance_lower in device_name:
                score += 0.5
            
            # Type match
            if device_type in utterance_lower:
                score += 0.3
            
            # Room context match
            if params.preferred_room_id and device_room_id == params.preferred_room_id:
                score += 0.2
            elif device_room_id in room_map:
                room_name = room_map[device_room_id]
                if room_name in utterance_lower:
                    score += 0.2
            
            # Word overlap scoring
            utterance_words = set(utterance_lower.split())
            device_words = set(device_name.split())
            overlap = utterance_words.intersection(device_words)
            if overlap:
                score += 0.1 * len(overlap)
            
            if score > 0:
                matches.append({
                    "device": device,
                    "score": min(score, 1.0)
                })
        
        # Sort by score
        matches.sort(key=lambda x: x["score"], reverse=True)
        
        if not matches:
            response = {
                "resolved": False,
                "confidence": 0.0,
                "original_utterance": params.utterance,
                "message": "No devices matched the description",
                "help": "Try using crestron_list_devices to see available devices"
            }
        elif matches[0]["score"] >= 0.8:
            # High confidence match
            device = matches[0]["device"]
            response = {
                "resolved": True,
                "confidence": matches[0]["score"],
                "device_id": device["id"],
                "device_name": device["name"],
                "device_type": device["type"],
                "room_id": device.get("roomId"),
                "original_utterance": params.utterance,
                "message": "Device successfully resolved"
            }
        else:
            # Multiple candidates - need clarification
            candidates = []
            for match in matches[:5]:  # Top 5 candidates
                device = match["device"]
                candidates.append({
                    "device_id": device["id"],
                    "name": device["name"],
                    "type": device["type"],
                    "subType": device.get("subType"),
                    "room_id": device.get("roomId"),
                    "confidence": round(match["score"], 2)
                })
            
            response = {
                "resolved": False,
                "confidence": matches[0]["score"],
                "original_utterance": params.utterance,
                "clarification_needed": True,
                "candidates": candidates,
                "message": (
                    f"Found {len(candidates)} possible matches. Please clarify which device you mean "
                    "by providing more specific information (room name, device type, etc.)"
                )
            }
        
        return json.dumps(response, indent=2)
        
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to resolve device",
            "details": str(e)
        }, indent=2)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Run the MCP server with stdio transport
    mcp.run()
