"""
Content Tracker Module

Tracks all content (instructions, rules, workflows, prompts) managed by team-config tool.
Enables automatic cleanup of managed content while preserving manually added files.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from schemas import ContentType

logger = logging.getLogger(__name__)


class ContentTracker:
    """Tracks managed content files for cleanup and management"""
    
    MANAGED_MARKER_FILE = ".team-config-managed.json"
    
    def __init__(self, state_dir: Optional[Path] = None):
        """
        Initialize content tracker
        
        Args:
            state_dir: Directory to store state files (defaults to ~/.mcp-team-config/state)
        """
        self.state_dir = state_dir or Path.home() / ".mcp-team-config" / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_content_statefile(self, profile_name: str) -> Path:
        """
        Get path to content statefile for a profile
        
        Args:
            profile_name: Profile name
        
        Returns:
            Path to statefile
        """
        return self.state_dir / f"content_{profile_name}.json"
    
    def _read_managed_content(self, profile_name: str) -> Dict[str, Any]:
        """
        Read managed content state from file
        
        Args:
            profile_name: Profile name
        
        Returns:
            Dictionary with managed content information
        """
        statefile = self._get_content_statefile(profile_name)
        
        if not statefile.exists():
            return {
                "profile": profile_name,
                "updated_at": None,
                "content": {
                    "instructions": {},
                    "rules": {},
                    "workflows": {},
                    "prompts": {}
                }
            }
        
        try:
            with open(statefile, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read content statefile: {e}")
            return {
                "profile": profile_name,
                "updated_at": None,
                "content": {
                    "instructions": {},
                    "rules": {},
                    "workflows": {},
                    "prompts": {}
                }
            }
    
    def _write_managed_content(self, profile_name: str, content_state: Dict[str, Any]) -> bool:
        """
        Write managed content state to file
        
        Args:
            profile_name: Profile name
            content_state: Content state dictionary
        
        Returns:
            True if successful, False otherwise
        """
        statefile = self._get_content_statefile(profile_name)
        
        try:
            with open(statefile, 'w', encoding='utf-8') as f:
                json.dump(content_state, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to write content statefile: {e}")
            return False
    
    def _create_marker_file(self, content_dir: Path, content_type: str, files: List[str]) -> bool:
        """
        Create a marker file in the content directory to identify managed files
        
        Args:
            content_dir: Directory containing content (e.g., profile_dir/instructions)
            content_type: Type of content (instructions, rules, workflows, prompts)
            files: List of managed file paths
        
        Returns:
            True if successful, False otherwise
        """
        marker_path = content_dir / self.MANAGED_MARKER_FILE
        
        try:
            marker_data = {
                "managed_by": "team-config",
                "content_type": content_type,
                "created_at": datetime.now().isoformat(),
                "files": files
            }
            
            with open(marker_path, 'w', encoding='utf-8') as f:
                json.dump(marker_data, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to create marker file: {e}")
            return False
    
    def _read_marker_file(self, content_dir: Path) -> Optional[Dict[str, Any]]:
        """
        Read marker file from content directory
        
        Args:
            content_dir: Directory containing content
        
        Returns:
            Marker data or None if not found
        """
        marker_path = content_dir / self.MANAGED_MARKER_FILE
        
        if not marker_path.exists():
            return None
        
        try:
            with open(marker_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read marker file: {e}")
            return None
    
    def cleanup_managed_content(
        self,
        profile_name: str,
        profile_dir: Path,
        current_content: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, int]:
        """
        Clean up managed content that is no longer in the profile
        
        Args:
            profile_name: Profile name
            profile_dir: Profile content directory
            current_content: Dictionary of current content by type
        
        Returns:
            Dictionary with count of files removed per content type
        """
        removed_counts = {
            "instructions": 0,
            "rules": 0,
            "workflows": 0,
            "prompts": 0
        }
        
        # Read previous managed content
        previous_state = self._read_managed_content(profile_name)
        
        for content_type in ["instructions", "rules", "workflows", "prompts"]:
            content_dir = profile_dir / content_type
            
            if not content_dir.exists():
                continue
            
            # Get previously managed files
            previous_files = set(previous_state.get("content", {}).get(content_type, {}).keys())
            
            # Get current files from this sync
            current_files = set()
            for item in current_content.get(content_type, []):
                file_path = Path(item["file"])
                current_files.add(str(file_path))
            
            # Files to remove: previously managed but not in current sync
            files_to_remove = previous_files - current_files
            
            # Also check marker file for additional safety
            marker_data = self._read_marker_file(content_dir)
            if marker_data:
                marker_files = set(marker_data.get("files", []))
                # Only remove files that are both in previous state AND marker file
                files_to_remove = files_to_remove.intersection(marker_files)
            
            # Remove old managed files
            for file_path_str in files_to_remove:
                file_path = Path(file_path_str)
                if file_path.exists():
                    try:
                        file_path.unlink()
                        removed_counts[content_type] += 1
                        logger.info(f"Removed managed {content_type} file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to remove {file_path}: {e}")
        
        return removed_counts
    
    def track_content(
        self,
        profile_name: str,
        profile_dir: Path,
        content: Dict[str, List[Dict[str, Any]]]
    ) -> bool:
        """
        Track newly synced content
        
        Args:
            profile_name: Profile name
            profile_dir: Profile content directory
            content: Dictionary of synced content by type
        
        Returns:
            True if successful, False otherwise
        """
        # Build new state
        new_state = {
            "profile": profile_name,
            "updated_at": datetime.now().isoformat(),
            "content": {}
        }
        
        for content_type in ["instructions", "rules", "workflows", "prompts"]:
            content_dir = profile_dir / content_type
            content_files = {}
            file_list = []
            
            for item in content.get(content_type, []):
                file_path = item["file"]
                content_files[file_path] = {
                    "source": item.get("source", "unknown"),
                    "size": item.get("size", 0),
                    "added_at": datetime.now().isoformat()
                }
                file_list.append(file_path)
            
            new_state["content"][content_type] = content_files
            
            # Create marker file in each content directory
            if content_dir.exists() and file_list:
                self._create_marker_file(content_dir, content_type, file_list)
        
        # Write state
        return self._write_managed_content(profile_name, new_state)
    
    def get_managed_files(self, profile_name: str, content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get list of managed files for a profile
        
        Args:
            profile_name: Profile name
            content_type: Optional content type filter
        
        Returns:
            Dictionary of managed files
        """
        state = self._read_managed_content(profile_name)
        
        if content_type:
            return state.get("content", {}).get(content_type, {})
        
        return state.get("content", {})
    
    def is_file_managed(self, profile_name: str, file_path: Path) -> bool:
        """
        Check if a file is managed by team-config
        
        Args:
            profile_name: Profile name
            file_path: Path to file
        
        Returns:
            True if file is managed, False otherwise
        """
        state = self._read_managed_content(profile_name)
        file_path_str = str(file_path)
        
        for content_type in ["instructions", "rules", "workflows", "prompts"]:
            if file_path_str in state.get("content", {}).get(content_type, {}):
                return True
        
        return False
    
    def clear_profile_tracking(self, profile_name: str) -> bool:
        """
        Clear all tracking for a profile
        
        Args:
            profile_name: Profile name
        
        Returns:
            True if successful, False otherwise
        """
        statefile = self._get_content_statefile(profile_name)
        
        try:
            if statefile.exists():
                statefile.unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to clear profile tracking: {e}")
            return False


def create_content_tracker(state_dir: Optional[Path] = None) -> ContentTracker:
    """
    Create a content tracker instance
    
    Args:
        state_dir: Optional state directory
    
    Returns:
        ContentTracker instance
    """
    return ContentTracker(state_dir)
