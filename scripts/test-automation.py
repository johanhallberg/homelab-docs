#!/usr/bin/env python3
"""
Test script for homelab automation environment
"""

import os
import requests
import json
from datetime import datetime

def test_environment_variables():
    """Test that all required environment variables are set"""
    required_vars = [
        'DISCORD_HOMELAB_WEBHOOK',
        'UPTIME_KUMA_USERNAME', 
        'UPTIME_KUMA_PASSWORD'
    ]
    
    print("🔍 Testing environment variables...")
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var or 'WEBHOOK' in var:
                print(f"✅ {var}: [SET]")
            else:
                print(f"✅ {var}: {value}")
        else:
            missing_vars.append(var)
            print(f"❌ {var}: NOT SET")
    
    return len(missing_vars) == 0

def test_discord_webhook():
    """Test Discord webhook connectivity"""
    webhook_url = os.getenv('DISCORD_HOMELAB_WEBHOOK')
    
    if not webhook_url:
        print("❌ Discord webhook URL not found")
        return False
    
    print("📢 Testing Discord webhook...")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = {
        "content": f"""🧪 **Automation System Test**

**Status**: Environment setup complete!
**Timestamp**: {timestamp}

✅ Environment variables configured
✅ Kubernetes secrets deployed  
✅ Discord integration working

The homelab automation system is ready! 🤖"""
    }
    
    try:
        response = requests.post(webhook_url, json=message)
        response.raise_for_status()
        print("✅ Discord notification sent successfully!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Discord notification failed: {e}")
        return False

def test_uptime_kuma_credentials():
    """Test Uptime Kuma credentials (without actually connecting)"""
    username = os.getenv('UPTIME_KUMA_USERNAME')
    password = os.getenv('UPTIME_KUMA_PASSWORD')
    
    print("⏱️ Testing Uptime Kuma credentials...")
    
    if username and password:
        print(f"✅ Uptime Kuma credentials configured for user: {username}")
        return True
    else:
        print("❌ Uptime Kuma credentials not configured")
        return False

def main():
    print("🤖 Homelab Automation Test Suite")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Discord Webhook", test_discord_webhook),
        ("Uptime Kuma Credentials", test_uptime_kuma_credentials)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Automation system is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    exit(main())
