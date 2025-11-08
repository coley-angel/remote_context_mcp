"""
Configuration Loader Module

Loads and parses team configuration files into structured data models
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
from schemas import (
    TeamConfig, Profile, RemoteSource, SecurityConfig, MCPServerConfig,
    SecurityLevel, IDEType, ContentType, FrontmatterConfig
)

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loads and validates team configuration"""
    
    @staticmethod
    def load_from_file(file_path: Path) -> Optional[TeamConfig]:
        """
        Load configuration from YAML file
        
        Args:
            file_path: Path to configuration file
        
        Returns:
            TeamConfig object or None if failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if data is None:
                logger.error(f"Empty YAML file: {file_path}")
                return None
            
            if not isinstance(data, dict):
                logger.error(f"Invalid YAML structure - expected dictionary, got {type(data)}: {file_path}")
                return None
            
            return ConfigLoader.parse_config(data)
        except yaml.YAMLError as e:
            logger.error(f"YAML syntax error in {file_path}")
            logger.error(f"  Error: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load config from {file_path}")
            logger.error(f"  Error type: {type(e).__name__}")
            logger.error(f"  Error message: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    @staticmethod
    def load_from_string(yaml_content: str) -> Optional[TeamConfig]:
        """
        Load configuration from YAML string
        
        Args:
            yaml_content: YAML configuration string
        
        Returns:
            TeamConfig object or None if failed
        """
        try:
            data = yaml.safe_load(yaml_content)
            
            if data is None:
                logger.error("Empty or invalid YAML content")
                return None
            
            if not isinstance(data, dict):
                logger.error(f"Invalid YAML structure - expected dictionary, got {type(data)}")
                return None
            
            return ConfigLoader.parse_config(data)
        except yaml.YAMLError as e:
            logger.error(f"YAML syntax error in content")
            logger.error(f"  Error: {e}")
            # Show first few lines of content for debugging
            lines = yaml_content.split('\n')[:5]
            logger.error(f"  First lines of content:\n" + "\n".join(f"    {line}" for line in lines))
            return None
        except Exception as e:
            logger.error(f"Failed to parse config from string")
            logger.error(f"  Error type: {type(e).__name__}")
            logger.error(f"  Error message: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    @staticmethod
    def parse_config(data: Dict[str, Any]) -> TeamConfig:
        """
        Parse configuration dictionary into TeamConfig object
        
        Args:
            data: Configuration dictionary
        
        Returns:
            TeamConfig object
        """
        # Parse global security
        global_security_data = data.get("global_security", {})
        global_security = ConfigLoader._parse_security_config(global_security_data)
        
        # Parse profiles
        profiles = {}
        profiles_data = data.get("profiles", {})
        for profile_name, profile_data in profiles_data.items():
            profiles[profile_name] = ConfigLoader._parse_profile(profile_name, profile_data)
        
        # Parse supported IDEs
        supported_ides = []
        for ide_str in data.get("supported_ides", ["vscode", "cursor", "windsurf"]):
            try:
                supported_ides.append(IDEType(ide_str))
            except ValueError:
                logger.warning(f"Unknown IDE type: {ide_str}")
        
        return TeamConfig(
            version=data.get("version", "1.0.0"),
            team_name=data.get("team_name", "default"),
            profiles=profiles,
            global_security=global_security,
            supported_ides=supported_ides,
            central_repo_url=data.get("central_repo_url"),
            central_repo_branch=data.get("central_repo_branch", "main"),
            auto_update=data.get("auto_update", True),
            update_check_interval_minutes=data.get("update_check_interval_minutes", 30),
            last_updated=data.get("last_updated"),
            updated_by=data.get("updated_by"),
        )
    
    @staticmethod
    def _parse_profile(name: str, data: Dict[str, Any]) -> Profile:
        """Parse profile data into Profile object"""
        # Parse remote sources
        instructions = ConfigLoader._parse_remote_sources(data.get("instructions", []))
        rules = ConfigLoader._parse_remote_sources(data.get("rules", []))
        workflows = ConfigLoader._parse_remote_sources(data.get("workflows", []))
        prompts = ConfigLoader._parse_remote_sources(data.get("prompts", []))
        
        # Parse MCP servers - support both list and dictionary formats
        mcp_servers = []
        mcp_servers_data = data.get("mcp_servers", [])
        
        if isinstance(mcp_servers_data, dict):
            # Dictionary format: {server_name: {config}}
            for server_name, server_config in mcp_servers_data.items():
                if isinstance(server_config, dict):
                    server_config = server_config.copy()
                    server_config["name"] = server_name
                    try:
                        mcp_servers.append(ConfigLoader._parse_mcp_server(server_config))
                    except Exception as e:
                        logger.warning(f"Failed to parse MCP server '{server_name}': {e}")
        elif isinstance(mcp_servers_data, list):
            # List format: [{name: server_name, ...}]
            for server_data in mcp_servers_data:
                try:
                    mcp_servers.append(ConfigLoader._parse_mcp_server(server_data))
                except Exception as e:
                    logger.warning(f"Failed to parse MCP server: {e}")
        
        # Parse IDE overrides
        ide_overrides = {}
        for ide_str, overrides in data.get("ide_overrides", {}).items():
            try:
                ide_type = IDEType(ide_str)
                ide_overrides[ide_type] = overrides
            except ValueError:
                logger.warning(f"Unknown IDE type in overrides: {ide_str}")
        
        # Parse security config
        security_data = data.get("security", {})
        security = ConfigLoader._parse_security_config(security_data)
        
        # Parse frontmatter defaults
        frontmatter_data = data.get("frontmatter_defaults", {})
        frontmatter_defaults = ConfigLoader._parse_frontmatter_config(frontmatter_data)
        
        # Parse central repo
        central_repo = None
        central_repo_data = data.get("central_repo")
        if central_repo_data:
            central_repo = ConfigLoader._parse_remote_source(central_repo_data)
        
        return Profile(
            name=name,
            active=data.get("active", False),
            description=data.get("description"),
            instructions=instructions,
            rules=rules,
            workflows=workflows,
            prompts=prompts,
            mcp_servers=mcp_servers,
            ide_overrides=ide_overrides,
            security=security,
            frontmatter_defaults=frontmatter_defaults,
            central_repo=central_repo,
            tags=data.get("tags", []),
        )
    
    @staticmethod
    def _parse_remote_sources(sources_data: List[Any]) -> List[RemoteSource]:
        """Parse list of remote sources"""
        sources = []
        for source_data in sources_data:
            source = ConfigLoader._parse_remote_source(source_data)
            if source:
                sources.append(source)
        return sources
    
    @staticmethod
    def _parse_remote_source(data: Any) -> Optional[RemoteSource]:
        """Parse single remote source"""
        if isinstance(data, str):
            # Simple URL string
            return RemoteSource(url=data)
        elif isinstance(data, dict):
            return RemoteSource(
                url=data.get("url"),
                repo=data.get("repo"),
                branch=data.get("branch", "main"),
                paths=data.get("paths", ["*.md"]),
                token_env_var=data.get("token_env_var"),
                auto_pull=data.get("auto_pull", True),
                pull_interval_minutes=data.get("pull_interval_minutes", 30),
            )
        return None
    
    @staticmethod
    def _parse_mcp_server(data: Dict[str, Any]) -> MCPServerConfig:
        """
        Parse MCP server configuration - supports multiple formats.
        Handles both standard format and IDE-native formats (Windsurf/VSCode/Cursor).
        """
        if "name" not in data:
            raise ValueError("MCP server configuration missing 'name' field")
        
        # Handle enabled/disabled field (IDEs use 'disabled', we use 'enabled')
        enabled = True
        if "disabled" in data:
            enabled = not data["disabled"]
        elif "enabled" in data:
            enabled = data["enabled"]
        
        # Command is required for standard servers but optional for HTTP/SSE
        command = data.get("command")
        args = data.get("args", [])
        server_type = data.get("type")
        
        # Parse command string if it contains spaces and no explicit args
        # "uvx package@version" -> command="uvx", args=["package@version"]
        if command and not args and ' ' in command:
            parts = command.split(None, 1)  # Split on first whitespace
            if len(parts) == 2:
                command, arg = parts
                args = [arg]
                logger.debug(f"Split command '{data.get('command')}' into command='{command}' args={args}")
        
        if not command and not (server_type or data.get("url")):
            logger.warning(f"MCP server '{data['name']}' has neither 'command' nor 'type/url'")
        
        return MCPServerConfig(
            name=data["name"],
            command=command,
            args=args,
            env=data.get("env", {}),
            cwd=data.get("cwd"),
            enabled=enabled,
            auto_restart=data.get("auto_restart", True),
            description=data.get("description"),
            # IDE-native fields
            type=server_type,
            url=data.get("url"),
            headers=data.get("headers"),
            inputs=data.get("inputs"),
            disabled=data.get("disabled"),
            autoApprove=data.get("autoApprove"),
        )
    
    @staticmethod
    def _parse_frontmatter_config(data: Dict[str, Any]) -> FrontmatterConfig:
        """Parse frontmatter configuration"""
        return FrontmatterConfig(
            trigger=data.get("trigger", "always_on"),
            glob=data.get("glob"),
            description=data.get("description"),
            priority=data.get("priority"),
            tags=data.get("tags", []),
            author=data.get("author"),
            version=data.get("version"),
        )
    
    @staticmethod
    def _parse_security_config(data: Dict[str, Any]) -> SecurityConfig:
        """Parse security configuration"""
        level = data.get("level", "basic")
        try:
            security_level = SecurityLevel(level)
        except ValueError:
            logger.warning(f"Unknown security level: {level}, using 'basic'")
            security_level = SecurityLevel.BASIC
        
        return SecurityConfig(
            enabled=data.get("enabled", True),
            level=security_level,
            forbidden_patterns=data.get("forbidden_patterns", []),
            required_patterns=data.get("required_patterns", []),
            max_file_size_kb=data.get("max_file_size_kb", 1024),
            allowed_domains=data.get("allowed_domains", []),
            scan_for_secrets=data.get("scan_for_secrets", True),
            scan_for_pii=data.get("scan_for_pii", True),
        )
    
    @staticmethod
    def save_to_file(config: TeamConfig, file_path: Path) -> bool:
        """
        Save configuration to YAML file
        
        Args:
            config: TeamConfig object
            file_path: Path to save to
        
        Returns:
            True if successful, False otherwise
        """
        try:
            data = ConfigLoader.config_to_dict(config)
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Saved configuration to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    @staticmethod
    def config_to_dict(config: TeamConfig) -> Dict[str, Any]:
        """
        Convert TeamConfig object to dictionary
        
        Args:
            config: TeamConfig object
        
        Returns:
            Configuration dictionary
        """
        data = {
            "version": config.version,
            "team_name": config.team_name,
            "central_repo_url": config.central_repo_url,
            "central_repo_branch": config.central_repo_branch,
            "auto_update": config.auto_update,
            "update_check_interval_minutes": config.update_check_interval_minutes,
            "global_security": ConfigLoader._security_to_dict(config.global_security),
            "supported_ides": [ide.value for ide in config.supported_ides],
            "profiles": {},
        }
        
        # Convert profiles
        for profile_name, profile in config.profiles.items():
            data["profiles"][profile_name] = ConfigLoader._profile_to_dict(profile)
        
        if config.last_updated:
            data["last_updated"] = config.last_updated
        if config.updated_by:
            data["updated_by"] = config.updated_by
        
        return data
    
    @staticmethod
    def _profile_to_dict(profile: Profile) -> Dict[str, Any]:
        """Convert Profile to dictionary"""
        data = {
            "active": profile.active,
            "description": profile.description,
            "instructions": [ConfigLoader._remote_source_to_dict(s) for s in profile.instructions],
            "rules": [ConfigLoader._remote_source_to_dict(s) for s in profile.rules],
            "workflows": [ConfigLoader._remote_source_to_dict(s) for s in profile.workflows],
            "prompts": [ConfigLoader._remote_source_to_dict(s) for s in profile.prompts],
            "mcp_servers": [ConfigLoader._mcp_server_to_dict(s) for s in profile.mcp_servers],
            "security": ConfigLoader._security_to_dict(profile.security),
            "tags": profile.tags,
        }
        
        if profile.ide_overrides:
            data["ide_overrides"] = {
                ide.value: overrides 
                for ide, overrides in profile.ide_overrides.items()
            }
        
        if profile.central_repo:
            data["central_repo"] = ConfigLoader._remote_source_to_dict(profile.central_repo)
        
        return data
    
    @staticmethod
    def _remote_source_to_dict(source: RemoteSource) -> Dict[str, Any]:
        """Convert RemoteSource to dictionary"""
        if source.url and not source.repo:
            # Simple URL format
            return source.url
        
        data = {}
        if source.url:
            data["url"] = source.url
        if source.repo:
            data["repo"] = source.repo
        if source.branch != "main":
            data["branch"] = source.branch
        if source.paths != ["*.md"]:
            data["paths"] = source.paths
        if source.token_env_var:
            data["token_env_var"] = source.token_env_var
        if not source.auto_pull:
            data["auto_pull"] = source.auto_pull
        if source.pull_interval_minutes != 30:
            data["pull_interval_minutes"] = source.pull_interval_minutes
        
        return data
    
    @staticmethod
    def _mcp_server_to_dict(server: MCPServerConfig) -> Dict[str, Any]:
        """Convert MCPServerConfig to dictionary"""
        data = {
            "name": server.name,
            "command": server.command,
            "enabled": server.enabled,
        }
        
        if server.args:
            data["args"] = server.args
        if server.env:
            data["env"] = server.env
        if server.cwd:
            data["cwd"] = server.cwd
        if not server.auto_restart:
            data["auto_restart"] = server.auto_restart
        if server.description:
            data["description"] = server.description
        
        return data
    
    @staticmethod
    def _security_to_dict(security: SecurityConfig) -> Dict[str, Any]:
        """Convert SecurityConfig to dictionary"""
        data = {
            "enabled": security.enabled,
            "level": security.level.value,
        }
        
        if security.forbidden_patterns:
            data["forbidden_patterns"] = security.forbidden_patterns
        if security.required_patterns:
            data["required_patterns"] = security.required_patterns
        if security.max_file_size_kb != 1024:
            data["max_file_size_kb"] = security.max_file_size_kb
        if security.allowed_domains:
            data["allowed_domains"] = security.allowed_domains
        if not security.scan_for_secrets:
            data["scan_for_secrets"] = security.scan_for_secrets
        if not security.scan_for_pii:
            data["scan_for_pii"] = security.scan_for_pii
        
        return data
