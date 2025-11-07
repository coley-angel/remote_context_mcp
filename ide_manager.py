"""
IDE Manager Module

Handles configuration updates for multiple IDEs:
- VS Code
- Cursor
- Windsurf

Manages:
- Settings files
- MCP server configurations
- Instruction file locations
- Rule files with frontmatter validation
"""
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from schemas import IDEType, IDEConfig, get_ide_config, MCPServerConfig
from frontmatter_utils import addFrontmatterToContent, validateFrontmatter, parseFrontmatter

logger = logging.getLogger(__name__)


class IDEManager:
    """Manages IDE-specific configurations"""
    
    MANAGED_MARKER = "_managed_by"
    MANAGED_VALUE = "team-config"
    
    def __init__(self, platform: Optional[str] = None, state_dir: Optional[Path] = None):
        """
        Initialize IDE manager
        
        Args:
            platform: Platform name (darwin, win32, linux) or None to auto-detect
            state_dir: Directory to store state files (defaults to ~/.mcp-team-config/state)
        """
        self.platform = platform or sys.platform
        self.ide_configs = {
            ide_type: get_ide_config(ide_type, self.platform)
            for ide_type in IDEType
        }
        self.state_dir = state_dir or Path.home() / ".mcp-team-config" / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def get_settings_path(self, ide_type: IDEType) -> Path:
        """
        Get the settings file path for an IDE
        
        Args:
            ide_type: IDE type
        
        Returns:
            Path to settings file
        """
        config = self.ide_configs[ide_type]
        return Path(config.settings_path).expanduser()
    
    def read_settings(self, ide_type: IDEType) -> Dict[str, Any]:
        """
        Read settings file for an IDE
        
        Args:
            ide_type: IDE type
        
        Returns:
            Settings dictionary
        """
        settings_path = self.get_settings_path(ide_type)
        
        if not settings_path.exists():
            logger.warning(f"{ide_type.value} settings file not found: {settings_path}")
            return {}
        
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {ide_type.value} settings: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to read {ide_type.value} settings: {e}")
            return {}
    
    def write_settings(self, ide_type: IDEType, settings: Dict[str, Any]) -> bool:
        """
        Write settings file for an IDE
        
        Args:
            ide_type: IDE type
            settings: Settings dictionary
        
        Returns:
            True if successful, False otherwise
        """
        settings_path = self.get_settings_path(ide_type)
        
        try:
            # Ensure directory exists
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write settings
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            
            logger.info(f"Updated {ide_type.value} settings: {settings_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write {ide_type.value} settings: {e}")
            return False
    
    def _get_instruction_statefile(self, ide_type: IDEType) -> Path:
        """
        Get path to instruction locations statefile
        
        Args:
            ide_type: IDE type
        
        Returns:
            Path to statefile
        """
        return self.state_dir / f"{ide_type.value}_managed_instructions.json"
    
    def _get_rules_statefile(self, ide_type: IDEType, workspace_dir: Optional[Path] = None) -> Path:
        """
        Get path to rules tracking statefile
        
        Args:
            ide_type: IDE type
            workspace_dir: Workspace directory (for workspace-specific tracking)
        
        Returns:
            Path to statefile
        """
        if workspace_dir:
            workspace_hash = abs(hash(str(workspace_dir))) % (10 ** 8)
            return self.state_dir / f"{ide_type.value}_rules_workspace_{workspace_hash}.json"
        else:
            return self.state_dir / f"{ide_type.value}_managed_rules.json"
    
    def _read_managed_instructions(self, ide_type: IDEType) -> Dict[str, Any]:
        """
        Read managed instruction locations from statefile
        
        Args:
            ide_type: IDE type
        
        Returns:
            Dictionary of managed instruction paths
        """
        statefile = self._get_instruction_statefile(ide_type)
        
        if not statefile.exists():
            return {"paths": {}}
        
        try:
            with open(statefile, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read instruction statefile: {e}")
            return {"paths": {}}
    
    def _write_managed_instructions(self, ide_type: IDEType, paths: Dict[str, bool]) -> bool:
        """
        Write managed instruction locations to statefile
        
        Args:
            ide_type: IDE type
            paths: Dictionary of managed instruction paths
        
        Returns:
            True if successful, False otherwise
        """
        statefile = self._get_instruction_statefile(ide_type)
        
        try:
            state = {
                "updated_at": datetime.now().isoformat(),
                "paths": paths
            }
            with open(statefile, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to write instruction statefile: {e}")
            return False
    
    def get_rules_path(self, ide_type: IDEType, workspace_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Get the rules directory path for an IDE
        
        Args:
            ide_type: IDE type
            workspace_dir: Workspace directory (for workspace-level rules)
        
        Returns:
            Path to rules directory or None if not supported
        """
        config = self.ide_configs[ide_type]
        
        if not config.rules_path:
            return None
        
        # Windsurf always uses global rules directory
        if ide_type == IDEType.WINDSURF:
            return Path(config.rules_path).expanduser()
        
        # VS Code and Cursor use workspace-level rules
        if workspace_dir:
            return workspace_dir / config.rules_path
        
        # No workspace provided for workspace-level IDEs
        return None
    
    def _track_managed_rules(
        self,
        ide_type: IDEType,
        profile_name: str,
        rule_files: set,
        workspace_dir: Optional[Path] = None
    ) -> bool:
        """
        Track managed rules for a profile
        
        Args:
            ide_type: IDE type
            profile_name: Profile name
            rule_files: Set of rule filenames
            workspace_dir: Workspace directory
        
        Returns:
            True if successful, False otherwise
        """
        statefile = self._get_rules_statefile(ide_type, workspace_dir)
        
        try:
            state = {
                "profile": profile_name,
                "updated_at": datetime.now().isoformat(),
                "rules": list(rule_files)
            }
            with open(statefile, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to track managed rules: {e}")
            return False
    
    def _read_managed_rules(self, ide_type: IDEType, workspace_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Read managed rules from statefile
        
        Args:
            ide_type: IDE type
            workspace_dir: Workspace directory
        
        Returns:
            Dictionary with managed rules state
        """
        statefile = self._get_rules_statefile(ide_type, workspace_dir)
        
        if not statefile.exists():
            return {"rules": []}
        
        try:
            with open(statefile, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read rules statefile: {e}")
            return {"rules": []}
    
    def cleanup_profile_rules(
        self,
        ide_type: IDEType,
        profile_name: str,
        workspace_dir: Optional[Path] = None
    ) -> bool:
        """
        Clean up rules when a profile is deactivated
        
        Args:
            ide_type: IDE type
            profile_name: Profile name being deactivated
            workspace_dir: Workspace directory
        
        Returns:
            True if successful, False otherwise
        """
        rules_dir = self.get_rules_path(ide_type, workspace_dir)
        
        if not rules_dir or not rules_dir.exists():
            return True
        
        try:
            # Read tracked rules
            state = self._read_managed_rules(ide_type, workspace_dir)
            
            if state.get("profile") != profile_name:
                logger.info(f"Skipping cleanup - different profile active")
                return True
            
            # Remove tracked rule files
            removed_count = 0
            for rule_filename in state.get("rules", []):
                rule_file = rules_dir / rule_filename
                if rule_file.exists():
                    rule_file.unlink()
                    removed_count += 1
                    logger.info(f"Removed rule file: {rule_file}")
            
            # Clear statefile
            statefile = self._get_rules_statefile(ide_type, workspace_dir)
            if statefile.exists():
                statefile.unlink()
            
            logger.info(f"Cleaned up {removed_count} rule files for profile '{profile_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup profile rules: {e}")
            return False
    
    def sync_rules_to_ide(
        self,
        ide_type: IDEType,
        rules_content: Dict[str, str],
        workspace_dir: Optional[Path] = None,
        profile_name: Optional[str] = None
    ) -> bool:
        """
        Sync rule files to IDE rules directory with frontmatter validation
        
        Args:
            ide_type: IDE type
            rules_content: Dictionary of {filename: content}
            workspace_dir: Workspace directory
            profile_name: Profile name for tracking
        
        Returns:
            True if successful, False otherwise
        """
        rules_dir = self.get_rules_path(ide_type, workspace_dir)
        
        if not rules_dir:
            logger.warning(f"{ide_type.value} does not support rules directory")
            return False
        
        try:
            # Create rules directory
            rules_dir.mkdir(parents=True, exist_ok=True)
            
            # Track synced rules for cleanup
            synced_files = set()
            
            # Write rule files with frontmatter validation
            for filename, content in rules_content.items():
                # Validate and add frontmatter if missing
                contentWithFrontmatter = addFrontmatterToContent(content)
                
                # Verify frontmatter was added
                frontmatter, _ = parseFrontmatter(contentWithFrontmatter)
                isValid, errorMsg = validateFrontmatter(frontmatter)
                
                if not isValid:
                    logger.warning(f"Rule {filename} has invalid frontmatter: {errorMsg}")
                    # Still write the file with attempted frontmatter fix
                
                rule_file = rules_dir / filename
                rule_file.write_text(contentWithFrontmatter, encoding='utf-8')
                synced_files.add(filename)
                logger.info(f"Synced rule to {ide_type.value}: {rule_file}")
            
            # Track managed rules for this profile
            if profile_name:
                self._track_managed_rules(ide_type, profile_name, synced_files, workspace_dir)
            
            return True
        except Exception as e:
            logger.error(f"Failed to sync rules to {ide_type.value}: {e}")
            return False
    
    def update_instruction_locations(
        self,
        ide_type: IDEType,
        locations: Dict[str, bool],
        track_managed: bool = True
    ) -> bool:
        """
        Update instruction file locations in IDE settings with tracking
        
        Args:
            ide_type: IDE type
            locations: Dictionary of {path: is_active} for new locations
            track_managed: If True, track these locations as managed
        
        Returns:
            True if successful, False otherwise
        """
        config = self.ide_configs[ide_type]
        settings = self.read_settings(ide_type)
        
        if track_managed:
            # Read previously managed locations
            previous_state = self._read_managed_instructions(ide_type)
            previous_paths = set(previous_state.get("paths", {}).keys())
            new_paths = set(locations.keys())
            
            # Get existing settings
            existing_locations = settings.get(config.instructions_key, {})
            
            # Remove previously managed paths that are no longer in new locations
            paths_to_remove = previous_paths - new_paths
            for path in paths_to_remove:
                existing_locations.pop(path, None)
                logger.info(f"Removed managed instruction location: {path}")
            
            # Add/update new managed paths
            existing_locations.update(locations)
            settings[config.instructions_key] = existing_locations
            
            # Track new managed paths
            self._write_managed_instructions(ide_type, locations)
        else:
            # Direct update without tracking
            settings[config.instructions_key] = locations
        
        return self.write_settings(ide_type, settings)
    
    def _get_mcp_servers_key(self, ide_type: IDEType) -> str:
        """
        Get the correct key name for MCP servers based on IDE type
        
        Args:
            ide_type: IDE type
        
        Returns:
            Key name for MCP servers in config ("mcpServers" for Windsurf, "servers" for others)
        """
        if ide_type == IDEType.WINDSURF:
            return "mcpServers"
        return "servers"
    
    def _get_statefile_path(self, ide_type: IDEType, workspace_dir: Optional[Path] = None) -> Path:
        """
        Get the path to the statefile for tracking managed servers
        
        Args:
            ide_type: IDE type
            workspace_dir: Workspace directory (for workspace-specific tracking)
        
        Returns:
            Path to statefile
        """
        if workspace_dir:
            # Workspace-specific statefile
            workspace_hash = abs(hash(str(workspace_dir))) % (10 ** 8)
            return self.state_dir / f"{ide_type.value}_workspace_{workspace_hash}.json"
        else:
            # Global statefile
            return self.state_dir / f"{ide_type.value}_managed_servers.json"
    
    def _read_managed_servers(self, ide_type: IDEType, workspace_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Read the list of managed servers from statefile
        
        Args:
            ide_type: IDE type
            workspace_dir: Workspace directory
        
        Returns:
            Dictionary of managed server names and metadata
        """
        statefile = self._get_statefile_path(ide_type, workspace_dir)
        
        if not statefile.exists():
            return {}
        
        try:
            with open(statefile, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read statefile: {e}")
            return {}
    
    def _write_managed_servers(self, ide_type: IDEType, managed_servers: Dict[str, Any], workspace_dir: Optional[Path] = None) -> bool:
        """
        Write the list of managed servers to statefile
        
        Args:
            ide_type: IDE type
            managed_servers: Dictionary of managed server names and metadata
            workspace_dir: Workspace directory
        
        Returns:
            True if successful, False otherwise
        """
        statefile = self._get_statefile_path(ide_type, workspace_dir)
        
        try:
            with open(statefile, 'w', encoding='utf-8') as f:
                json.dump(managed_servers, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to write statefile: {e}")
            return False
    
    def get_mcp_config_path(
        self,
        ide_type: IDEType,
        workspace_dir: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Get MCP configuration file path for an IDE
        
        Args:
            ide_type: IDE type
            workspace_dir: Workspace directory (required for workspace-level configs)
        
        Returns:
            Path to MCP config file or None if not supported
        """
        config = self.ide_configs[ide_type]
        
        if not config.mcp_config_path:
            return None
        
        # Windsurf always uses global config
        if ide_type == IDEType.WINDSURF:
            return Path(config.mcp_config_path).expanduser()
        
        if workspace_dir:
            # Workspace-level config
            return workspace_dir / config.mcp_config_path
        else:
            # Global config (if supported)
            settings_path = self.get_settings_path(ide_type)
            return settings_path.parent / "mcp.json"
    
    def read_mcp_config(
        self,
        ide_type: IDEType,
        workspace_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Read MCP configuration for an IDE
        
        Args:
            ide_type: IDE type
            workspace_dir: Workspace directory
        
        Returns:
            MCP configuration dictionary
        """
        mcp_path = self.get_mcp_config_path(ide_type, workspace_dir)
        servers_key = self._get_mcp_servers_key(ide_type)
        
        if not mcp_path or not mcp_path.exists():
            return {servers_key: {}}
        
        try:
            with open(mcp_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read MCP config: {e}")
            return {servers_key: {}}
    
    def write_mcp_config(
        self,
        ide_type: IDEType,
        config: Dict[str, Any],
        workspace_dir: Optional[Path] = None
    ) -> bool:
        """
        Write MCP configuration for an IDE
        
        Args:
            ide_type: IDE type
            config: MCP configuration dictionary
            workspace_dir: Workspace directory
        
        Returns:
            True if successful, False otherwise
        """
        mcp_path = self.get_mcp_config_path(ide_type, workspace_dir)
        
        if not mcp_path:
            logger.warning(f"{ide_type.value} does not support MCP configuration")
            return False
        
        try:
            # Ensure directory exists
            mcp_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write config
            with open(mcp_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Updated {ide_type.value} MCP config: {mcp_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write MCP config: {e}")
            return False
    
    def update_mcp_servers(
        self,
        ide_type: IDEType,
        servers: List[MCPServerConfig],
        workspace_dir: Optional[Path] = None,
        merge: bool = True,
        profile_name: Optional[str] = None
    ) -> bool:
        """
        Update MCP server configurations with tracking for managed servers
        
        Args:
            ide_type: IDE type
            servers: List of MCP server configurations from profile
            workspace_dir: Workspace directory
            merge: If True, merge with existing servers and remove previously managed servers not in profile;
                   if False, replace all servers
            profile_name: Name of the profile managing these servers
        
        Returns:
            True if successful, False otherwise
        """
        mcp_config = self.read_mcp_config(ide_type, workspace_dir)
        servers_key = self._get_mcp_servers_key(ide_type)
        existing_servers = mcp_config.get(servers_key, {})
        
        # Read current managed servers from statefile
        managed_servers_state = self._read_managed_servers(ide_type, workspace_dir)
        
        # Get list of previously managed server names
        previously_managed = set(managed_servers_state.get("servers", {}).keys())
        
        # Get list of new managed server names from profile
        new_managed_names = {server.name for server in servers if server.enabled}
        
        if merge:
            # Remove previously managed servers that are no longer in the profile
            servers_to_remove = previously_managed - new_managed_names
            for server_name in servers_to_remove:
                if server_name in existing_servers:
                    # Only remove if it still has the managed marker or is in our statefile
                    server_config = existing_servers[server_name]
                    if isinstance(server_config, dict) and server_config.get(self.MANAGED_MARKER) == self.MANAGED_VALUE:
                        logger.info(f"Removing managed server '{server_name}' (no longer in profile)")
                        existing_servers.pop(server_name)
                    elif server_name in previously_managed:
                        logger.info(f"Removing managed server '{server_name}' from statefile")
                        existing_servers.pop(server_name)
        else:
            # Replace mode: remove all previously managed servers
            for server_name in previously_managed:
                existing_servers.pop(server_name, None)
        
        # Add/update servers from profile
        new_managed_servers = {}
        for server in servers:
            if not server.enabled:
                continue
            
            server_config = {
                "command": server.command,
                "args": server.args,
                self.MANAGED_MARKER: self.MANAGED_VALUE,  # Mark as managed by team-config
            }
            
            if server.env:
                server_config["env"] = server.env
            
            if server.cwd:
                server_config["cwd"] = server.cwd
            
            existing_servers[server.name] = server_config
            
            # Track in statefile
            new_managed_servers[server.name] = {
                "profile": profile_name or "unknown",
                "added_at": datetime.now().isoformat(),
                "command": server.command
            }
        
        # Update statefile with current managed servers
        managed_state = {
            "profile": profile_name or "unknown",
            "updated_at": datetime.now().isoformat(),
            "servers": new_managed_servers
        }
        self._write_managed_servers(ide_type, managed_state, workspace_dir)
        
        # Write updated config
        mcp_config[servers_key] = existing_servers
        return self.write_mcp_config(ide_type, mcp_config, workspace_dir)
    
    def detect_installed_ides(self) -> List[IDEType]:
        """
        Detect which IDEs are installed
        
        Returns:
            List of installed IDE types
        """
        installed = []
        
        for ide_type in IDEType:
            settings_path = self.get_settings_path(ide_type)
            if settings_path.parent.exists():
                installed.append(ide_type)
        
        return installed
    
    def sync_to_all_ides(
        self,
        instruction_locations: Dict[str, bool],
        mcp_servers: Optional[List[MCPServerConfig]] = None,
        workspace_dir: Optional[Path] = None,
        profile_name: Optional[str] = None,
        rules_content: Optional[Dict[str, str]] = None
    ) -> Dict[IDEType, bool]:
        """
        Sync configurations to all detected IDEs
        
        Args:
            instruction_locations: Dictionary of instruction locations
            mcp_servers: Optional list of MCP server configurations
            workspace_dir: Optional workspace directory for MCP configs
            profile_name: Name of the profile managing these servers
            rules_content: Optional dictionary of {filename: content} for rule files
        
        Returns:
            Dictionary of {ide_type: success}
        """
        results = {}
        installed_ides = self.detect_installed_ides()
        
        for ide_type in installed_ides:
            try:
                # Update instruction locations
                success = self.update_instruction_locations(ide_type, instruction_locations)
                
                # Sync rule files if provided
                if rules_content and success:
                    success = self.sync_rules_to_ide(
                        ide_type,
                        rules_content,
                        workspace_dir,
                        profile_name
                    )
                
                # Update MCP servers if provided
                if mcp_servers is not None and success:
                    success = self.update_mcp_servers(
                        ide_type,
                        mcp_servers,
                        workspace_dir,
                        merge=True,
                        profile_name=profile_name
                    )
                
                results[ide_type] = success
                
                if success:
                    logger.info(f"Successfully synced to {ide_type.value}")
                else:
                    logger.warning(f"Failed to sync to {ide_type.value}")
                    
            except Exception as e:
                logger.error(f"Error syncing to {ide_type.value}: {e}")
                results[ide_type] = False
        
        return results
    
    def cleanup_all_ides(
        self,
        profile_name: str,
        workspace_dir: Optional[Path] = None
    ) -> Dict[IDEType, bool]:
        """
        Clean up rules from all detected IDEs for a profile
        
        Args:
            profile_name: Profile name to cleanup
            workspace_dir: Optional workspace directory
        
        Returns:
            Dictionary of {ide_type: success}
        """
        results = {}
        installed_ides = self.detect_installed_ides()
        
        for ide_type in installed_ides:
            try:
                success = self.cleanup_profile_rules(ide_type, profile_name, workspace_dir)
                results[ide_type] = success
                
                if success:
                    logger.info(f"Successfully cleaned up rules from {ide_type.value}")
                else:
                    logger.warning(f"Failed to cleanup rules from {ide_type.value}")
                    
            except Exception as e:
                logger.error(f"Error cleaning up {ide_type.value}: {e}")
                results[ide_type] = False
        
        return results
    
    def backup_settings(self, ide_type: IDEType) -> Optional[Path]:
        """
        Create a backup of IDE settings
        
        Args:
            ide_type: IDE type
        
        Returns:
            Path to backup file or None if failed
        """
        settings_path = self.get_settings_path(ide_type)
        
        if not settings_path.exists():
            return None
        
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = settings_path.parent / f"settings_backup_{timestamp}.json"
            
            import shutil
            shutil.copy2(settings_path, backup_path)
            
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to backup settings: {e}")
            return None
    
    def restore_settings(
        self,
        ide_type: IDEType,
        backup_path: Path
    ) -> bool:
        """
        Restore IDE settings from backup
        
        Args:
            ide_type: IDE type
            backup_path: Path to backup file
        
        Returns:
            True if successful, False otherwise
        """
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        settings_path = self.get_settings_path(ide_type)
        
        try:
            import shutil
            shutil.copy2(backup_path, settings_path)
            logger.info(f"Restored settings from: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore settings: {e}")
            return False


def create_ide_manager(platform: Optional[str] = None) -> IDEManager:
    """
    Create an IDE manager instance
    
    Args:
        platform: Platform name or None to auto-detect
    
    Returns:
        IDEManager instance
    """
    return IDEManager(platform)
