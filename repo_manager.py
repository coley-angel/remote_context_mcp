"""
Repository Manager Module

Handles Git repository operations for:
- Cloning central configuration repositories
- Pulling updates from remote repos
- Managing local cached copies
- Detecting changes and triggering updates
"""
import os
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import git
from git import Repo, GitCommandError

logger = logging.getLogger(__name__)


class RepoManager:
    """Manages Git repository operations for configuration syncing"""
    
    def __init__(self, cache_dir: Path):
        """
        Initialize repository manager
        
        Args:
            cache_dir: Directory for caching cloned repositories
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._repo_cache: Dict[str, Tuple[Repo, datetime]] = {}
    
    def get_repo_cache_path(self, repo_url: str, branch: str = "main") -> Path:
        """
        Get the cache path for a repository
        
        Args:
            repo_url: URL of the repository
            branch: Branch name
        
        Returns:
            Path to cached repository
        """
        # Create a unique hash for the repo URL and branch
        repo_hash = hashlib.md5(f"{repo_url}#{branch}".encode()).hexdigest()[:12]
        return self.cache_dir / f"repo_{repo_hash}"
    
    def clone_or_update_repo(
        self,
        repo_url: str,
        branch: str = "main",
        token: Optional[str] = None,
        force_update: bool = False
    ) -> Optional[Repo]:
        """
        Clone a repository or update existing clone
        
        Args:
            repo_url: URL of the repository
            branch: Branch to checkout
            token: Authentication token (for private repos)
            force_update: Force pull even if recently updated
        
        Returns:
            Git Repo object or None if failed
        """
        cache_path = self.get_repo_cache_path(repo_url, branch)
        
        # Check if we have a recent cached version
        cache_key = f"{repo_url}#{branch}"
        if cache_key in self._repo_cache and not force_update:
            repo, last_update = self._repo_cache[cache_key]
            # Only update if cached version is older than 5 minutes
            if datetime.now() - last_update < timedelta(minutes=5):
                logger.info(f"Using cached repository: {repo_url}")
                return repo
        
        try:
            # Inject token into URL for authentication
            auth_url = repo_url
            if token:
                auth_url = self._inject_token_in_url(repo_url, token)
            
            if cache_path.exists():
                # Repository exists, pull updates
                logger.info(f"Updating repository: {repo_url}")
                repo = Repo(cache_path)
                
                # Fetch and reset to remote branch
                origin = repo.remotes.origin
                origin.fetch()
                
                # Reset to remote branch
                try:
                    repo.git.reset('--hard', f'origin/{branch}')
                except GitCommandError:
                    # Branch might not exist, try to checkout
                    repo.git.checkout(branch)
                    repo.git.reset('--hard', f'origin/{branch}')
            else:
                # Clone the repository
                logger.info(f"Cloning repository: {repo_url}")
                repo = Repo.clone_from(
                    auth_url,
                    cache_path,
                    branch=branch,
                    depth=1  # Shallow clone for efficiency
                )
            
            # Cache the repo
            self._repo_cache[cache_key] = (repo, datetime.now())
            return repo
            
        except GitCommandError as e:
            logger.error(f"Git error for {repo_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to clone/update repository {repo_url}: {e}")
            return None
    
    def get_files_from_repo(
        self,
        repo: Repo,
        path_patterns: List[str]
    ) -> List[Path]:
        """
        Get files from repository matching path patterns
        
        Args:
            repo: Git repository object
            path_patterns: List of glob patterns to match
        
        Returns:
            List of file paths
        """
        files = []
        repo_path = Path(repo.working_dir)
        
        for pattern in path_patterns:
            # Support both glob patterns and exact paths
            if "*" in pattern or "?" in pattern:
                # Glob pattern
                matched_files = list(repo_path.glob(pattern))
                files.extend([f for f in matched_files if f.is_file()])
            else:
                # Exact path
                file_path = repo_path / pattern
                if file_path.exists() and file_path.is_file():
                    files.append(file_path)
        
        return files
    
    def get_repo_info(self, repo: Repo) -> Dict[str, Any]:
        """
        Get information about a repository
        
        Args:
            repo: Git repository object
        
        Returns:
            Dictionary with repo information
        """
        try:
            return {
                "path": repo.working_dir,
                "branch": repo.active_branch.name,
                "commit": repo.head.commit.hexsha[:8],
                "commit_message": repo.head.commit.message.strip(),
                "commit_date": repo.head.commit.committed_datetime.isoformat(),
                "is_dirty": repo.is_dirty(),
            }
        except Exception as e:
            logger.error(f"Failed to get repo info: {e}")
            return {}
    
    def check_for_updates(
        self,
        repo_url: str,
        branch: str = "main",
        token: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if repository has updates without pulling
        
        Args:
            repo_url: URL of the repository
            branch: Branch to check
            token: Authentication token
        
        Returns:
            Tuple of (has_updates, latest_commit_hash)
        """
        cache_path = self.get_repo_cache_path(repo_url, branch)
        
        if not cache_path.exists():
            return True, None  # Not cloned yet, so has "updates"
        
        try:
            repo = Repo(cache_path)
            
            # Get current commit
            current_commit = repo.head.commit.hexsha
            
            # Fetch latest from remote
            origin = repo.remotes.origin
            origin.fetch()
            
            # Get remote commit
            remote_commit = repo.commit(f'origin/{branch}').hexsha
            
            has_updates = current_commit != remote_commit
            return has_updates, remote_commit
            
        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
            return False, None
    
    def _inject_token_in_url(self, url: str, token: str) -> str:
        """
        Inject authentication token into Git URL
        
        Args:
            url: Git repository URL
            token: Authentication token
        
        Returns:
            URL with embedded token
        """
        # Handle GitHub URLs
        if "github.com" in url:
            if url.startswith("https://"):
                return url.replace("https://", f"https://{token}@")
            elif url.startswith("git@"):
                # Convert SSH to HTTPS
                url = url.replace("git@github.com:", "https://github.com/")
                return url.replace("https://", f"https://{token}@")
        
        # Handle other Git hosting services similarly
        if url.startswith("https://"):
            return url.replace("https://", f"https://{token}@")
        
        return url
    
    def clear_cache(self, repo_url: Optional[str] = None):
        """
        Clear repository cache
        
        Args:
            repo_url: Specific repo to clear, or None to clear all
        """
        if repo_url:
            cache_key = f"{repo_url}#main"
            if cache_key in self._repo_cache:
                del self._repo_cache[cache_key]
            
            cache_path = self.get_repo_cache_path(repo_url)
            if cache_path.exists():
                import shutil
                shutil.rmtree(cache_path)
                logger.info(f"Cleared cache for {repo_url}")
        else:
            self._repo_cache.clear()
            import shutil
            for item in self.cache_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
            logger.info("Cleared all repository cache")
    
    def get_file_content(
        self,
        repo: Repo,
        file_path: str
    ) -> Optional[str]:
        """
        Get content of a file from repository
        
        Args:
            repo: Git repository object
            file_path: Path to file relative to repo root
        
        Returns:
            File content or None if not found
        """
        try:
            full_path = Path(repo.working_dir) / file_path
            if full_path.exists() and full_path.is_file():
                return full_path.read_text(encoding='utf-8')
            return None
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None
    
    def list_changed_files(
        self,
        repo: Repo,
        since_commit: Optional[str] = None
    ) -> List[str]:
        """
        List files changed since a specific commit
        
        Args:
            repo: Git repository object
            since_commit: Commit hash to compare against (or None for all files)
        
        Returns:
            List of changed file paths
        """
        try:
            if since_commit:
                # Get diff between commits
                diff = repo.commit(since_commit).diff(repo.head.commit)
                return [item.a_path for item in diff]
            else:
                # Return all tracked files
                return [item.path for item in repo.tree().traverse() if item.type == 'blob']
        except Exception as e:
            logger.error(f"Failed to list changed files: {e}")
            return []


def create_repo_manager(cache_dir: Optional[Path] = None) -> RepoManager:
    """
    Create a repository manager instance
    
    Args:
        cache_dir: Directory for caching repos (defaults to ~/.mcp-config-cache)
    
    Returns:
        RepoManager instance
    """
    if cache_dir is None:
        cache_dir = Path.home() / ".mcp-config-cache" / "repos"
    
    return RepoManager(cache_dir)
