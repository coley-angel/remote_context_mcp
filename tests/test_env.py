#!/usr/bin/env python3
"""Test script to check environment variables"""
import os
import sys
from pathlib import Path

print("=" * 80, file=sys.stderr)
print("Environment Variable Test", file=sys.stderr)
print("=" * 80, file=sys.stderr)
print(f"GITHUB_TOKEN: {'SET' if os.getenv('GITHUB_TOKEN') else 'NOT SET'}", file=sys.stderr)
print(f"TEAM_CONFIG_REPO: {os.getenv('TEAM_CONFIG_REPO', 'NOT SET')}", file=sys.stderr)
print(f"TEAM_CONFIG_FILE: {os.getenv('TEAM_CONFIG_FILE', 'NOT SET')}", file=sys.stderr)
print(f"TEAM_CONFIG_BRANCH: {os.getenv('TEAM_CONFIG_BRANCH', 'NOT SET')}", file=sys.stderr)
print(f"Working directory: {os.getcwd()}", file=sys.stderr)
print(f"Script location: {Path(__file__).parent}", file=sys.stderr)
print("=" * 80, file=sys.stderr)
