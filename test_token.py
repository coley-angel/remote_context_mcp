#!/usr/bin/env python3
import os
import httpx
import base64

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "CiscoOpsStack/Ops_Stack_Dev_Profiles"
FILE = "team_config.yaml"
BRANCH = "main"

print(f"Testing GitHub access...")
print(f"Token: {'SET' if GITHUB_TOKEN else 'NOT SET'}")

url = f"https://api.github.com/repos/{REPO}/contents/{FILE}?ref={BRANCH}"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
} if GITHUB_TOKEN else {}

response = httpx.get(url, headers=headers, timeout=10.0)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    print("✓ SUCCESS - Can fetch config!")
    data = response.json()
    content = base64.b64decode(data['content']).decode('utf-8')
    print(f"Config size: {len(content)} bytes")
    
    import yaml
    config = yaml.safe_load(content)
    print(f"Team: {config.get('team_name')}")
    print(f"Profiles: {list(config.get('profiles', {}).keys())}")
elif response.status_code == 404:
    print("❌ NOT FOUND - File doesn't exist or wrong path")
elif response.status_code == 401:
    print("❌ UNAUTHORIZED - Token invalid or missing")
else:
    print(f"❌ ERROR: {response.text[:200]}")
