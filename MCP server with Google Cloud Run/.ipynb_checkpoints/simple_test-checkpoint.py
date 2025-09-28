"""
Simple test to verify the MCP server is working
"""

import requests
import json

def test_server_health():
    """Test if the server is responding"""
    
    # Update this URL with your deployed service URL
    server_url = "https://weather-mcp-server-937447787060.us-central1.run.app"
    
    # You can also set this via environment variable:
    # export MCP_SERVER_URL=https://your-service-url
    import os
    server_url = os.getenv("MCP_SERVER_URL", server_url)
    
    print("🌤️ Testing Weather Intelligence MCP Server")
    print("=" * 60)
    print(f"Server URL: {server_url}")
    print()
    
    # Test 1: Basic connectivity
    print("🔍 Test 1: Basic server connectivity...")
    try:
        response = requests.get(f"{server_url}/mcp/", timeout=10)
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        if response.text:
            print(f"   Response: {response.text[:200]}...")
        print("   ✅ Server is responding!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
    
    print()
    
    # Test 2: Try MCP initialize request
    print("🔍 Test 2: MCP Initialize request...")
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream'
        }
        
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = requests.post(
            f"{server_url}/mcp/",
            headers=headers,
            json=initialize_request,
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.text:
            try:
                result = response.json()
                print(f"   Response: {json.dumps(result, indent=2)}")
            except:
                print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("   ✅ MCP Initialize successful!")
        else:
            print("   ⚠️  MCP Initialize returned non-200 status")
            
    except Exception as e:
        print(f"   ❌ MCP Initialize failed: {e}")
    
    print()
    print("🎉 Basic connectivity tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_server_health()