#!/usr/bin/env python3
"""
Create Uptime Kuma monitor for docs.hallonen.se
"""

import requests
import json
import os
import sys

def create_monitor():
    """Create a monitor for docs.hallonen.se in Uptime Kuma"""
    
    # Uptime Kuma configuration
    base_url = "https://uptime.staging.hallonen.se"
    username = os.getenv('UPTIME_KUMA_USERNAME')
    password = os.getenv('UPTIME_KUMA_PASSWORD')
    
    if not username or not password:
        print("❌ Uptime Kuma credentials are not set. Ensure UPTIME_KUMA_USERNAME and UPTIME_KUMA_PASSWORD are configured.")
        return False
    
    print("🔍 Creating Uptime Kuma monitor for docs.hallonen.se...")
    
    # Note: Uptime Kuma typically uses WebSocket for real-time API communication
    # For now, we'll try the HTTP API endpoints and fall back to manual setup
    
    session = requests.Session()
    
    try:
        # Try different possible API endpoints
        api_endpoints = [
            f"{base_url}/api/login",
            f"{base_url}/login", 
            f"{base_url}/api/auth/login"
        ]
        
        login_success = False
        for endpoint in api_endpoints:
            try:
                login_payload = {"username": username, "password": password}
                login_response = session.post(endpoint, json=login_payload)
                if login_response.status_code == 200:
                    print(f"🔑 Successfully logged in to Uptime Kuma via {endpoint}")
                    login_success = True
                    break
            except:
                continue
        
        if not login_success:
            print("⚠️ Could not authenticate via HTTP API - Uptime Kuma typically uses WebSocket")
            print("📋 Will provide manual setup instructions instead")
            return False
        
        # If login was successful, try to create monitor
        monitor_payload = {
            "name": "docs.hallonen.se",
            "url": "https://docs.hallonen.se",
            "type": "http",
            "interval": 60,
            "maxretries": 3,
            "timeout": 30,
            "retryInterval": 60,
            "httpBodyEncoding": "json",
            "expectedStatus": "200-299",
            "followRedirect": True,
            "ignoreTls": False,
            "acceptedStatusCodes": ["200-299"],
            "httpMethod": "GET",
            "description": "Homelab documentation site via Cloudflare tunnel",
            "tags": ["production", "documentation", "cloudflare-tunnel"]
        }
        
        monitor_endpoints = [
            f"{base_url}/api/monitor",
            f"{base_url}/api/monitors"
        ]
        
        for endpoint in monitor_endpoints:
            try:
                create_response = session.post(endpoint, json=monitor_payload)
                if create_response.status_code in [200, 201]:
                    print("✅ Successfully created Uptime Kuma monitor via API")
                    return True
            except:
                continue
        
        print("⚠️ Could not create monitor via API - falling back to manual setup")
        return False

    except Exception as e:
        print(f"❌ API communication failed: {e}")
        print("📋 Will provide manual setup instructions")
        return False
    finally:
        session.close()
    
    # For now, just validate that the service is accessible
    print("\n🌐 Testing service accessibility...")
    try:
        response = requests.get("https://docs.hallonen.se", timeout=10)
        if response.status_code == 200:
            print(f"✅ Service is accessible - Status: {response.status_code}")
            print(f"📏 Response size: {len(response.content)} bytes")
            
            # Check if it contains expected content
            if "homelab" in response.text.lower() or "documentation" in response.text.lower():
                print("📖 Content validation: Documentation content detected")
            else:
                print("⚠️ Content validation: Expected documentation content not found")
                
        else:
            print(f"❌ Service returned status: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Service is not accessible: {e}")
        return False
    
    print("\n📋 Manual Setup Instructions (if API creation failed):")
    print("=" * 50)
    print("1. Access Uptime Kuma at: https://uptime.staging.hallonen.se")
    print("2. Login with your credentials")
    print("3. Click 'Add New Monitor'")
    print("4. Configure with the following settings:")
    print(f"   - Monitor Type: HTTP(s)")
    print(f"   - Friendly Name: docs.hallonen.se")
    print(f"   - URL: https://docs.hallonen.se")
    print(f"   - Heartbeat Interval: 60 seconds")
    print(f"   - Retries: 3")
    print(f"   - HTTP Method: GET")
    print(f"   - Accepted Status Codes: 200-299")
    print("5. Click 'Save'")
    
    return True

def send_notification():
    """Send Discord notification about monitor setup"""
    webhook_url = os.getenv('DISCORD_HOMELAB_WEBHOOK')
    
    if not webhook_url:
        print("💬 Discord webhook not configured, skipping notification")
        return
        
    message = {
        "content": """📊 **Uptime Kuma Monitor Ready**

**Service**: docs.hallonen.se
**Status**: Accessible and ready for monitoring
**Access**: http://192.168.100.200:30080

Manual monitor setup instructions provided. The production documentation site is now ready for automated uptime monitoring! 📈"""
    }
    
    try:
        response = requests.post(webhook_url, json=message)
        response.raise_for_status()
        print("📢 Discord notification sent!")
    except requests.exceptions.RequestException as e:
        print(f"❌ Discord notification failed: {e}")

def main():
    print("🤖 Uptime Kuma Monitor Setup for docs.hallonen.se")
    print("=" * 60)
    
    if create_monitor():
        send_notification()
        print("\n✅ Monitor setup completed successfully!")
        return 0
    else:
        print("\n❌ Monitor setup failed!")
        return 1

if __name__ == "__main__":
    exit(main())
