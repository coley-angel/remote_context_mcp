#!/usr/bin/env python3
"""
Team Config Validator

Validates team_config.yaml files and provides detailed error messages and corrections.
Supports both V1 and V2 formats, with recommendations to upgrade to V2.
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import json

@dataclass
class ValidationIssue:
    """A validation issue with severity and fix suggestion"""
    level: str  # "error", "warning", "info"
    field: str
    message: str
    current_value: Any
    suggested_fix: Optional[str] = None
    
    def __str__(self):
        icon = "❌" if self.level == "error" else "⚠️" if self.level == "warning" else "ℹ️"
        result = f"{icon} [{self.level.upper()}] {self.field}: {self.message}"
        if self.current_value is not None:
            result += f"\n   Current: {self.current_value}"
        if self.suggested_fix:
            result += f"\n   Fix: {self.suggested_fix}"
        return result


class ConfigValidator:
    """Validates team configuration files"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.issues: List[ValidationIssue] = []
        self.stats = {
            "errors": 0,
            "warnings": 0,
            "info": 0
        }
    
    def add_issue(self, level: str, field: str, message: str, current_value: Any = None, suggested_fix: str = None):
        """Add a validation issue"""
        issue = ValidationIssue(level, field, message, current_value, suggested_fix)
        self.issues.append(issue)
        self.stats[f"{level}s"] = self.stats.get(f"{level}s", 0) + 1
    
    def validate_file(self, file_path: Path) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate a team config YAML file
        
        Returns:
            (is_valid, config_data)
        """
        print(f"\n{'='*70}")
        print(f"VALIDATING: {file_path}")
        print(f"{'='*70}\n")
        
        # Check file exists
        if not file_path.exists():
            self.add_issue("error", "file", f"File not found: {file_path}", None)
            return False, {}
        
        # Load YAML
        try:
            with open(file_path, 'r') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.add_issue("error", "yaml", f"Invalid YAML syntax: {e}", None)
            return False, {}
        except Exception as e:
            self.add_issue("error", "file", f"Could not read file: {e}", None)
            return False, {}
        
        if not config:
            self.add_issue("error", "content", "File is empty", None)
            return False, {}
        
        # Detect version
        version = config.get("version", "1.0.0")
        is_v2 = version.startswith("2.")
        
        print(f"📋 Detected version: {version} ({'V2' if is_v2 else 'V1'})")
        if not is_v2:
            self.add_issue("warning", "version", 
                          "Using V1 config format",
                          version,
                          "Upgrade to version: '2.0.0' for new features")
        print()
        
        # Validate based on version
        if is_v2:
            self._validate_v2_config(config)
        else:
            self._validate_v1_config(config)
        
        # Print results
        self._print_results()
        
        is_valid = self.stats["errors"] == 0
        return is_valid, config
    
    def _validate_v1_config(self, config: Dict[str, Any]):
        """Validate V1 format config"""
        print("🔍 Validating V1 format...\n")
        
        # Required fields
        required = ["team_name", "profiles"]
        for field in required:
            if field not in config:
                self.add_issue("error", field, f"Required field missing", None,
                             f"Add '{field}:' to config")
        
        # Team name
        if "team_name" in config:
            if not config["team_name"] or not isinstance(config["team_name"], str):
                self.add_issue("error", "team_name", "Must be a non-empty string", 
                             config.get("team_name"))
        
        # Supported IDEs
        if "supported_ides" in config:
            valid_ides = {"vscode", "cursor", "windsurf"}
            for ide in config["supported_ides"]:
                if ide not in valid_ides:
                    self.add_issue("warning", "supported_ides", 
                                 f"Unknown IDE: {ide}", ide,
                                 f"Use one of: {', '.join(valid_ides)}")
        
        # Profiles
        if "profiles" in config:
            if not isinstance(config["profiles"], dict):
                self.add_issue("error", "profiles", "Must be a dictionary", 
                             type(config["profiles"]))
            else:
                self._validate_v1_profiles(config["profiles"])
        
        # V2 recommendation
        self.add_issue("info", "upgrade", 
                      "Consider upgrading to V2 format",
                      None,
                      "V2 adds IDE-specific configs, better file tracking, and simplified architecture")
    
    def _validate_v2_config(self, config: Dict[str, Any]):
        """Validate V2 format config"""
        print("🔍 Validating V2 format...\n")
        
        # Required fields
        required = ["version", "team_name", "profiles"]
        for field in required:
            if field not in config:
                self.add_issue("error", field, f"Required field missing", None,
                             f"Add '{field}:' to config")
        
        # Version check
        if "version" in config:
            if not config["version"].startswith("2."):
                self.add_issue("error", "version", 
                             "Version should be 2.x for V2 format",
                             config["version"],
                             "Set version: '2.0.0'")
        
        # Team name
        if "team_name" in config:
            if not config["team_name"] or not isinstance(config["team_name"], str):
                self.add_issue("error", "team_name", "Must be a non-empty string", 
                             config.get("team_name"))
        
        # Profiles
        if "profiles" in config:
            if not isinstance(config["profiles"], dict):
                self.add_issue("error", "profiles", "Must be a dictionary", 
                             type(config["profiles"]))
            else:
                self._validate_v2_profiles(config["profiles"])
    
    def _validate_v1_profiles(self, profiles: Dict[str, Any]):
        """Validate V1 profile structure"""
        if not profiles:
            self.add_issue("error", "profiles", "At least one profile required", None)
            return
        
        active_count = 0
        for name, profile in profiles.items():
            if not isinstance(profile, dict):
                self.add_issue("error", f"profiles.{name}", 
                             "Profile must be a dictionary", type(profile))
                continue
            
            # Check active status
            if profile.get("active", False):
                active_count += 1
            
            # Check content sources
            for content_type in ["rules", "workflows", "prompts", "instructions"]:
                if content_type in profile:
                    if not isinstance(profile[content_type], list):
                        self.add_issue("error", f"profiles.{name}.{content_type}",
                                     "Must be a list", type(profile[content_type]))
                    else:
                        self._validate_content_sources(profile[content_type], 
                                                      f"profiles.{name}.{content_type}")
            
            # V2 upgrade suggestion
            if "ide_configs" not in profile:
                self.add_issue("info", f"profiles.{name}",
                             "Missing ide_configs (V2 feature)",
                             None,
                             "Add ide_configs with windsurf, vscode, cursor configurations")
        
        # Active profile check
        if active_count == 0:
            self.add_issue("warning", "profiles", 
                         "No active profile", None,
                         "Set 'active: true' for one profile")
        elif active_count > 1:
            self.add_issue("warning", "profiles",
                         f"Multiple active profiles ({active_count})", None,
                         "Only one profile should be active")
    
    def _validate_v2_profiles(self, profiles: Dict[str, Any]):
        """Validate V2 profile structure"""
        if not profiles:
            self.add_issue("error", "profiles", "At least one profile required", None)
            return
        
        active_count = 0
        for name, profile in profiles.items():
            if not isinstance(profile, dict):
                self.add_issue("error", f"profiles.{name}", 
                             "Profile must be a dictionary", type(profile))
                continue
            
            # Check active status
            if profile.get("active", False):
                active_count += 1
            
            # Check IDE configs (V2 required)
            if "ide_configs" not in profile:
                self.add_issue("warning", f"profiles.{name}.ide_configs",
                             "Missing IDE configs (V2 feature)", None,
                             "Add ide_configs with windsurf, vscode, cursor")
            else:
                self._validate_ide_configs(profile["ide_configs"], 
                                          f"profiles.{name}.ide_configs")
            
            # Check content sources
            for content_type in ["rules", "workflows", "prompts", "instructions"]:
                if content_type in profile:
                    if not isinstance(profile[content_type], list):
                        self.add_issue("error", f"profiles.{name}.{content_type}",
                                     "Must be a list", type(profile[content_type]))
                    else:
                        self._validate_content_sources(profile[content_type], 
                                                      f"profiles.{name}.{content_type}")
        
        # Active profile check
        if active_count == 0:
            self.add_issue("warning", "profiles", 
                         "No active profile", None,
                         "Set 'active: true' for one profile")
        elif active_count > 1:
            self.add_issue("warning", "profiles",
                         f"Multiple active profiles ({active_count})", None,
                         "Only one profile should be active")
    
    def _validate_ide_configs(self, ide_configs: Dict[str, Any], path: str):
        """Validate IDE configurations"""
        if not isinstance(ide_configs, dict):
            self.add_issue("error", path, "Must be a dictionary", type(ide_configs))
            return
        
        valid_ides = {"windsurf", "vscode", "cursor"}
        for ide_name, ide_config in ide_configs.items():
            if ide_name not in valid_ides:
                self.add_issue("warning", f"{path}.{ide_name}",
                             f"Unknown IDE name", ide_name,
                             f"Use one of: {', '.join(valid_ides)}")
            
            if not isinstance(ide_config, dict):
                self.add_issue("error", f"{path}.{ide_name}",
                             "IDE config must be a dictionary", type(ide_config))
                continue
            
            # Check required fields
            if "paths" not in ide_config:
                self.add_issue("error", f"{path}.{ide_name}.paths",
                             "Missing paths configuration", None,
                             "Add paths: { rules: '.{ide}/rules', workflows: ... }")
            else:
                self._validate_ide_paths(ide_config["paths"], 
                                        f"{path}.{ide_name}.paths")
            
            # Check optional frontmatter
            if "frontmatter_defaults" in ide_config:
                self._validate_frontmatter(ide_config["frontmatter_defaults"],
                                          f"{path}.{ide_name}.frontmatter_defaults")
    
    def _validate_ide_paths(self, paths: Dict[str, Any], path: str):
        """Validate IDE paths"""
        if not isinstance(paths, dict):
            self.add_issue("error", path, "Must be a dictionary", type(paths))
            return
        
        required_paths = ["rules", "workflows", "prompts", "instructions"]
        for path_type in required_paths:
            if path_type not in paths:
                self.add_issue("warning", f"{path}.{path_type}",
                             "Missing path configuration", None,
                             f"Add {path_type}: '.ide/{path_type}'")
            else:
                path_value = paths[path_type]
                if not isinstance(path_value, str):
                    self.add_issue("error", f"{path}.{path_type}",
                                 "Path must be a string", type(path_value))
                elif path_value.startswith('/') or path_value.startswith('~'):
                    self.add_issue("error", f"{path}.{path_type}",
                                 "Path must be relative, not absolute",
                                 path_value,
                                 f"Use relative path like '.ide/{path_type}'")
    
    def _validate_frontmatter(self, frontmatter: Dict[str, Any], path: str):
        """Validate frontmatter defaults"""
        if not isinstance(frontmatter, dict):
            self.add_issue("error", path, "Must be a dictionary", type(frontmatter))
            return
        
        # Valid trigger values
        if "trigger" in frontmatter:
            valid_triggers = {"always_on", "manual", "on_demand"}
            if frontmatter["trigger"] not in valid_triggers:
                self.add_issue("warning", f"{path}.trigger",
                             f"Unknown trigger value: {frontmatter['trigger']}",
                             frontmatter["trigger"],
                             f"Use one of: {', '.join(valid_triggers)}")
        
        # Valid priority values
        if "priority" in frontmatter:
            valid_priorities = {"critical", "high", "medium", "low"}
            if frontmatter["priority"] not in valid_priorities:
                self.add_issue("warning", f"{path}.priority",
                             f"Unknown priority: {frontmatter['priority']}",
                             frontmatter["priority"],
                             f"Use one of: {', '.join(valid_priorities)}")
    
    def _validate_content_sources(self, sources: List[Any], path: str):
        """Validate content source list"""
        for idx, source in enumerate(sources):
            if not isinstance(source, dict):
                self.add_issue("error", f"{path}[{idx}]",
                             "Source must be a dictionary", type(source))
                continue
            
            # Check for repo or url
            if "repo" not in source and "url" not in source:
                self.add_issue("error", f"{path}[{idx}]",
                             "Source must have 'repo' or 'url' field", None,
                             "Add 'repo: org/repo' or 'url: https://...'")
            
            # Validate repo format
            if "repo" in source:
                repo = source["repo"]
                if "/" not in repo or repo.startswith("http"):
                    self.add_issue("warning", f"{path}[{idx}].repo",
                                 "Repo should be in 'org/repo' format", repo,
                                 "Use format: 'CiscoOpsStack/MyRepo'")
            
            # Check paths
            if "paths" in source:
                if not isinstance(source["paths"], list):
                    self.add_issue("error", f"{path}[{idx}].paths",
                                 "Paths must be a list", type(source["paths"]))
    
    def _print_results(self):
        """Print validation results"""
        print("\n" + "="*70)
        print("VALIDATION RESULTS")
        print("="*70 + "\n")
        
        if not self.issues:
            print("✅ No issues found! Config is valid.\n")
            return
        
        # Group by level
        errors = [i for i in self.issues if i.level == "error"]
        warnings = [i for i in self.issues if i.level == "warning"]
        infos = [i for i in self.issues if i.level == "info"]
        
        # Print errors
        if errors:
            print(f"❌ ERRORS ({len(errors)}):")
            print("-" * 70)
            for issue in errors:
                print(f"{issue}\n")
        
        # Print warnings
        if warnings:
            print(f"⚠️  WARNINGS ({len(warnings)}):")
            print("-" * 70)
            for issue in warnings:
                print(f"{issue}\n")
        
        # Print info
        if infos:
            print(f"ℹ️  INFO ({len(infos)}):")
            print("-" * 70)
            for issue in infos:
                print(f"{issue}\n")
        
        # Summary
        print("="*70)
        print("SUMMARY:")
        print(f"  Errors:   {len(errors)}")
        print(f"  Warnings: {len(warnings)}")
        print(f"  Info:     {len(infos)}")
        print(f"  Status:   {'❌ INVALID' if errors else '⚠️  VALID (with warnings)' if warnings else '✅ VALID'}")
        print("="*70 + "\n")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python validate_config.py <config-file.yaml>")
        print("\nExample:")
        print("  python validate_config.py team_config.yaml")
        print("  python validate_config.py /path/to/team_config.yaml")
        sys.exit(1)
    
    config_path = Path(sys.argv[1])
    validator = ConfigValidator(verbose=True)
    is_valid, config = validator.validate_file(config_path)
    
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
