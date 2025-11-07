#!/usr/bin/env python
"""
Test script for Team Configuration MCP Server
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import (
    load_team_config,
    get_ide_manager,
    get_security_validator,
    get_repo_manager,
    create_default_config
)
from config_loader import ConfigLoader
from schemas import IDEType

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_configuration():
    """Test configuration loading"""
    print_section("Testing Configuration System")
    
    try:
        config = load_team_config()
        print(f"✅ Configuration loaded")
        print(f"   Team: {config.team_name}")
        print(f"   Version: {config.version}")
        print(f"   Profiles: {len(config.profiles)}")
        
        active_profiles = [p.name for p in config.profiles.values() if p.active]
        print(f"   Active: {active_profiles}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_security_validator():
    """Test security validation"""
    print_section("Testing Security Validation")
    
    try:
        config = load_team_config()
        validator = get_security_validator(config)
        
        tests = [
            ("Clean content", "This is clean content", True),
            ("AWS Key", "AKIA1234567890ABCDEF", False),
            ("Email", "test@example.com", True),  # Example email allowed
            ("Password", 'password="mysecret123"', False),
        ]
        
        passed = 0
        for name, content, should_pass in tests:
            is_valid, violations = validator.validate_content(content, "test.md", "instruction")
            
            if should_pass:
                if is_valid or len([v for v in violations if v.severity == "critical"]) == 0:
                    print(f"✅ {name}: Passed")
                    passed += 1
                else:
                    print(f"❌ {name}: Should pass but failed")
            else:
                if not is_valid:
                    print(f"✅ {name}: Correctly detected issue")
                    passed += 1
                else:
                    print(f"❌ {name}: Should fail but passed")
        
        print(f"\n   Passed: {passed}/{len(tests)}")
        return passed == len(tests)
    except Exception as e:
        print(f"❌ Security validation test failed: {e}")
        return False

def test_ide_manager():
    """Test IDE manager"""
    print_section("Testing IDE Manager")
    
    try:
        ide_mgr = get_ide_manager()
        
        # Test IDE detection
        installed = ide_mgr.detect_installed_ides()
        print(f"✅ Detected IDEs: {[ide.value for ide in installed]}")
        
        # Test settings paths
        for ide_type in installed:
            settings_path = ide_mgr.get_settings_path(ide_type)
            exists = settings_path.exists()
            status = "✅" if exists else "⚠️"
            print(f"   {status} {ide_type.value}: {settings_path}")
        
        return len(installed) > 0
    except Exception as e:
        print(f"❌ IDE manager test failed: {e}")
        return False


def test_ide_detection():
    """Test IDE detection features"""
    print_section("Testing IDE Detection")
    
    try:
        from main import detect_current_ide, get_current_ide, set_current_ide, get_ide_content_dir
        from schemas import IDEType
        
        # Test automatic detection
        detected = detect_current_ide()
        if detected:
            print(f"✅ Auto-detected IDE: {detected.value}")
        else:
            print(f"⚠️  No IDE auto-detected (this is OK)")
        
        # Test get current IDE (with fallback)
        current = get_current_ide()
        print(f"✅ Current IDE: {current.value}")
        
        # Test setting IDE explicitly
        set_current_ide(IDEType.WINDSURF)
        current = get_current_ide()
        if current == IDEType.WINDSURF:
            print(f"✅ IDE set to: {current.value}")
        else:
            print(f"❌ Failed to set IDE")
            return False
        
        # Test IDE-specific content directories
        for ide_type in [IDEType.VSCODE, IDEType.CURSOR, IDEType.WINDSURF]:
            content_dir = get_ide_content_dir(ide_type, "test-profile")
            print(f"   {ide_type.value}: {content_dir}")
        
        return True
    except Exception as e:
        print(f"❌ IDE detection test failed: {e}")
        return False

def test_repo_manager():
    """Test repository manager"""
    print_section("Testing Repository Manager")
    
    try:
        repo_mgr = get_repo_manager()
        
        # Test cache path generation
        test_url = "https://github.com/test/repo"
        cache_path = repo_mgr.get_repo_cache_path(test_url, "main")
        
        print(f"✅ Cache path generated: {cache_path}")
        print(f"   Cache directory exists: {cache_path.parent.exists()}")
        
        return True
    except Exception as e:
        print(f"❌ Repository manager test failed: {e}")
        return False

def test_config_loader():
    """Test configuration loader"""
    print_section("Testing Configuration Loader")
    
    try:
        # Test creating default config
        config = create_default_config()
        print(f"✅ Default config created")
        print(f"   Team: {config.team_name}")
        print(f"   Profiles: {len(config.profiles)}")
        
        # Test serialization
        config_dict = ConfigLoader.config_to_dict(config)
        print(f"✅ Config serialization works")
        print(f"   Keys: {list(config_dict.keys())}")
        
        return True
    except Exception as e:
        print(f"❌ Config loader test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  TEAM CONFIGURATION MCP SERVER - TEST SUITE")
    print("="*60)
    
    tests = [
        ("Configuration System", test_configuration),
        ("Security Validation", test_security_validator),
        ("IDE Manager", test_ide_manager),
        ("IDE Detection", test_ide_detection),
        ("Repository Manager", test_repo_manager),
        ("Config Loader", test_config_loader),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test {name} crashed: {e}")
            results.append((name, False))
    
    # Print summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 All tests passed!")
        return 0
    else:
        print(f"\n  ⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
