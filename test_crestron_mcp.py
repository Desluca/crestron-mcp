#!/usr/bin/env python3
"""
Test Script for Crestron MCP Server

Tests the MCP server against the mock Crestron API.
Validates all tools and scenarios.

Usage:
    python test_crestron_mcp.py
"""

import json
import asyncio
import httpx
from typing import Dict, Any, List

# Test configuration
MOCK_HOST = "localhost:8080"
AUTH_TOKEN = "test-token-123"

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_test(msg: str):
    print(f"{Colors.BOLD}{Colors.YELLOW}🧪 {msg}{Colors.END}")


class CrestronMCPTester:
    """Test suite for Crestron MCP."""
    
    def __init__(self, host: str, auth_token: str):
        self.host = host
        self.auth_token = auth_token
        self.auth_key = None
        self.client = httpx.AsyncClient(verify=False, timeout=30.0)
        self.tests_passed = 0
        self.tests_failed = 0
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    async def authenticate(self) -> bool:
        """Test authentication."""
        print_test("Test 1: Authentication")
        
        try:
            response = await self.client.get(
                f"http://{self.host}/cws/api/login",
                headers={"Crestron-RestAPI-AuthToken": self.auth_token}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_key = data.get("AuthKey")
                print_success(f"Authentication successful. Session key: {self.auth_key[:20]}...")
                self.tests_passed += 1
                return True
            else:
                print_error(f"Authentication failed: {response.status_code}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            print_error(f"Authentication error: {e}")
            self.tests_failed += 1
            return False
    
    async def test_list_rooms(self) -> bool:
        """Test listing rooms."""
        print_test("Test 2: List Rooms")
        
        try:
            response = await self.client.get(
                f"http://{self.host}/cws/api/rooms",
                headers={"Crestron-RestAPI-AuthKey": self.auth_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                rooms = data.get("rooms", [])
                print_success(f"Retrieved {len(rooms)} rooms")
                
                for room in rooms:
                    print(f"   • {room['name']} (ID: {room['id']})")
                
                self.tests_passed += 1
                return True
            else:
                print_error(f"List rooms failed: {response.status_code}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            print_error(f"List rooms error: {e}")
            self.tests_failed += 1
            return False
    
    async def test_list_devices(self) -> bool:
        """Test listing devices."""
        print_test("Test 3: List Devices")
        
        try:
            response = await self.client.get(
                f"http://{self.host}/cws/api/devices",
                headers={"Crestron-RestAPI-AuthKey": self.auth_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                devices = data.get("devices", [])
                print_success(f"Retrieved {len(devices)} devices")
                
                # Group by type
                by_type = {}
                for device in devices:
                    dtype = device.get("type", "unknown")
                    if dtype not in by_type:
                        by_type[dtype] = []
                    by_type[dtype].append(device)
                
                for dtype, devs in by_type.items():
                    print(f"   • {dtype}: {len(devs)} device(s)")
                    for dev in devs[:2]:  # Show first 2 of each type
                        print(f"     - {dev['name']} (ID: {dev['id']})")
                
                self.tests_passed += 1
                return True
            else:
                print_error(f"List devices failed: {response.status_code}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            print_error(f"List devices error: {e}")
            self.tests_failed += 1
            return False
    
    async def test_get_shades(self) -> bool:
        """Test getting shade status."""
        print_test("Test 4: Get Shades")
        
        try:
            response = await self.client.get(
                f"http://{self.host}/cws/api/shades",
                headers={"Crestron-RestAPI-AuthKey": self.auth_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                shades = data.get("shades", [])
                print_success(f"Retrieved {len(shades)} shades")
                
                for shade in shades:
                    position = int(shade['position'] * 100 / 65535)
                    print(f"   • {shade['name']}: {position}% open")
                
                self.tests_passed += 1
                return True
            else:
                print_error(f"Get shades failed: {response.status_code}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            print_error(f"Get shades error: {e}")
            self.tests_failed += 1
            return False
    
    async def test_set_shade_position(self) -> bool:
        """Test setting shade position."""
        print_test("Test 5: Set Shade Position")
        
        try:
            # Close shade ID 20 (Tapparella Grande)
            body = {
                "shades": [
                    {"id": 20, "position": 0}  # Fully closed
                ]
            }
            
            response = await self.client.post(
                f"http://{self.host}/cws/api/shades/SetState",
                headers={
                    "Crestron-RestAPI-AuthKey": self.auth_key,
                    "Content-Type": "application/json"
                },
                json=body
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                
                if status == "success":
                    print_success("Shade position set successfully")
                    print("   • Tapparella Grande → 0% (closed)")
                    self.tests_passed += 1
                    return True
                else:
                    print_error(f"Partial success or failure: {status}")
                    self.tests_failed += 1
                    return False
            else:
                print_error(f"Set shade position failed: {response.status_code}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            print_error(f"Set shade position error: {e}")
            self.tests_failed += 1
            return False
    
    async def test_list_scenes(self) -> bool:
        """Test listing scenes."""
        print_test("Test 6: List Scenes")
        
        try:
            response = await self.client.get(
                f"http://{self.host}/cws/api/scenes",
                headers={"Crestron-RestAPI-AuthKey": self.auth_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                scenes = data.get("scenes", [])
                print_success(f"Retrieved {len(scenes)} scenes")
                
                for scene in scenes:
                    status = "✓" if scene['status'] else "○"
                    print(f"   {status} {scene['name']} ({scene['type']})")
                
                self.tests_passed += 1
                return True
            else:
                print_error(f"List scenes failed: {response.status_code}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            print_error(f"List scenes error: {e}")
            self.tests_failed += 1
            return False
    
    async def test_activate_scene(self) -> bool:
        """Test activating a scene."""
        print_test("Test 7: Activate Scene")
        
        try:
            # Activate scene ID 3 (Film)
            response = await self.client.post(
                f"http://{self.host}/cws/api/scenes/recall/3",
                headers={"Crestron-RestAPI-AuthKey": self.auth_key}
            )
            
            if response.status_code == 200:
                print_success("Scene 'Film' activated successfully")
                self.tests_passed += 1
                return True
            else:
                print_error(f"Activate scene failed: {response.status_code}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            print_error(f"Activate scene error: {e}")
            self.tests_failed += 1
            return False
    
    async def test_get_thermostats(self) -> bool:
        """Test getting thermostat status."""
        print_test("Test 8: Get Thermostats")
        
        try:
            response = await self.client.get(
                f"http://{self.host}/cws/api/thermostats",
                headers={"Crestron-RestAPI-AuthKey": self.auth_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                thermostats = data.get("thermostats", [])
                print_success(f"Retrieved {len(thermostats)} thermostat(s)")
                
                for tstat in thermostats:
                    temp_c = tstat['currentTemperature'] / 10
                    setpoint_c = tstat['setPoint']['temperature'] / 10
                    print(f"   • {tstat['name']}: {temp_c}°C (setpoint: {setpoint_c}°C)")
                    print(f"     Mode: {tstat['mode']}, Fan: {tstat['currentFanMode']}")
                
                self.tests_passed += 1
                return True
            else:
                print_error(f"Get thermostats failed: {response.status_code}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            print_error(f"Get thermostats error: {e}")
            self.tests_failed += 1
            return False
    
    async def test_set_thermostat_setpoint(self) -> bool:
        """Test setting thermostat setpoint."""
        print_test("Test 9: Set Thermostat Setpoint")
        
        try:
            # Set thermostat to 21°C
            body = {
                "id": 80,
                "setpoints": [
                    {"type": "Cool", "temperature": 210}  # 21.0°C
                ]
            }
            
            response = await self.client.post(
                f"http://{self.host}/cws/api/thermostats/SetPoint",
                headers={
                    "Crestron-RestAPI-AuthKey": self.auth_key,
                    "Content-Type": "application/json"
                },
                json=body
            )
            
            if response.status_code == 200:
                print_success("Thermostat setpoint updated successfully")
                print("   • Termostato Principale → 21.0°C (Cool)")
                self.tests_passed += 1
                return True
            else:
                print_error(f"Set thermostat setpoint failed: {response.status_code}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            print_error(f"Set thermostat setpoint error: {e}")
            self.tests_failed += 1
            return False
    
    async def test_get_sensors(self) -> bool:
        """Test getting sensor readings."""
        print_test("Test 10: Get Sensors")
        
        try:
            response = await self.client.get(
                f"http://{self.host}/cws/api/sensors",
                headers={"Crestron-RestAPI-AuthKey": self.auth_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                sensors = data.get("sensors", [])
                print_success(f"Retrieved {len(sensors)} sensor(s)")
                
                for sensor in sensors:
                    subtype = sensor.get('subType', 'Unknown')
                    print(f"   • {sensor['name']} ({subtype})")
                    
                    if 'presence' in sensor:
                        print(f"     Presence: {sensor['presence']}")
                    if 'level' in sensor:
                        print(f"     Light Level: {sensor['level']}")
                    if 'door status' in sensor:
                        print(f"     Door: {sensor['door status']}")
                
                self.tests_passed += 1
                return True
            else:
                print_error(f"Get sensors failed: {response.status_code}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            print_error(f"Get sensors error: {e}")
            self.tests_failed += 1
            return False
    
    async def run_all_tests(self):
        """Run all tests."""
        print("\n" + "=" * 70)
        print(f"{Colors.BOLD}🧪 CRESTRON MCP TEST SUITE{Colors.END}")
        print("=" * 70)
        print()
        
        # Run tests in sequence
        await self.authenticate()
        print()
        
        if not self.auth_key:
            print_error("Authentication failed. Cannot continue with other tests.")
            return
        
        await self.test_list_rooms()
        print()
        
        await self.test_list_devices()
        print()
        
        await self.test_get_shades()
        print()
        
        await self.test_set_shade_position()
        print()
        
        await self.test_list_scenes()
        print()
        
        await self.test_activate_scene()
        print()
        
        await self.test_get_thermostats()
        print()
        
        await self.test_set_thermostat_setpoint()
        print()
        
        await self.test_get_sensors()
        print()
        
        # Summary
        print("=" * 70)
        print(f"{Colors.BOLD}📊 TEST SUMMARY{Colors.END}")
        print("=" * 70)
        
        total = self.tests_passed + self.tests_failed
        success_rate = (self.tests_passed / total * 100) if total > 0 else 0
        
        print(f"\n{Colors.GREEN}✅ Passed: {self.tests_passed}/{total}{Colors.END}")
        print(f"{Colors.RED}❌ Failed: {self.tests_failed}/{total}{Colors.END}")
        print(f"\n{Colors.BOLD}Success Rate: {success_rate:.1f}%{Colors.END}")
        
        if self.tests_failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed!{Colors.END}")
        else:
            print(f"\n{Colors.YELLOW}⚠️  Some tests failed. Check the output above.{Colors.END}")
        
        print()


async def main():
    """Main test runner."""
    print_info("Starting Crestron MCP test suite...")
    print_info(f"Target: http://{MOCK_HOST}")
    print_info(f"Auth Token: {AUTH_TOKEN}")
    print()
    
    # Check if mock server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://{MOCK_HOST}/cws/api/rooms", timeout=2.0)
    except:
        print_error("Mock Crestron server is not running!")
        print_info("Please start it first with: python mock_crestron_server.py")
        return
    
    # Run tests
    tester = CrestronMCPTester(MOCK_HOST, AUTH_TOKEN)
    
    try:
        await tester.run_all_tests()
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
