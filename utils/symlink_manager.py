"""
Symlink Manager for ComfyUI
Creates symbolic links from /share/ directory to ComfyUI project directories
"""

import os
import logging
from pathlib import Path
from typing import List, Set


class SymlinkManager:
    """Manages symbolic links from /share/ directory to ComfyUI project"""
    
    def __init__(self, project_root: str, share_directory: str = "/share"):
        """
        Initialize the SymlinkManager
        
        Args:
            project_root: Path to ComfyUI project root directory
            share_directory: Path to the share directory (default: /share)
        """
        self.project_root = Path(project_root).resolve()
        self.share_directory = Path(share_directory).resolve()
        self.logger = logging.getLogger(__name__)
        
        # Define the directories that should be linked from /share/
        self.target_directories = {
            "models",
            "custom_nodes", 
            "input",
            "output",
            "user"
        }
    
    def create_symlinks(self) -> None:
        """
        Create symbolic links from /share/ directory to ComfyUI project directories
        Supports both top-level directory symlinks and deep file/directory symlinks
        Skips if target already exists in project
        """
        if not self.share_directory.exists():
            self.logger.warning(f"Share directory {self.share_directory} does not exist, skipping symlink creation")
            return
        
        self.logger.info(f"Checking for directories to link from {self.share_directory} to {self.project_root}")
        
        created_links = []
        skipped_items = []
        
        # First, try to create deep symlinks for files and subdirectories
        deep_links = self._create_deep_symlinks()
        created_links.extend(deep_links)
        
        # Then, create top-level directory symlinks for directories that weren't processed
        for target_dir in self.target_directories:
            share_path = self.share_directory / target_dir
            project_path = self.project_root / target_dir
            
            # Skip if we already processed this directory with deep linking
            if project_path.exists() and not project_path.is_symlink():
                self.logger.debug(f"Skipping top-level symlink for {target_dir} (already processed with deep linking)")
                continue
                
            if self._should_create_symlink(share_path, project_path):
                if self._create_symlink(share_path, project_path):
                    created_links.append(target_dir)
                else:
                    skipped_items.append(target_dir)
            else:
                skipped_items.append(target_dir)
        
        if created_links:
            self.logger.info(f"Successfully created symlinks for: {', '.join(created_links)}")
        
        if skipped_items:
            self.logger.info(f"Skipped items (already exist or not found in share): {', '.join(skipped_items)}")
    
    def _should_create_symlink(self, share_path: Path, project_path: Path) -> bool:
        """
        Check if a symlink should be created
        
        Args:
            share_path: Path in /share/ directory
            project_path: Target path in project directory
            
        Returns:
            True if symlink should be created, False otherwise
        """
        # Check if source exists in /share/
        if not share_path.exists():
            self.logger.debug(f"Source {share_path} does not exist in share directory")
            return False
        
        # Check if target already exists in project
        if project_path.exists():
            self.logger.debug(f"Target {project_path} already exists, skipping")
            return False
        
        return True
    
    def _create_symlink(self, source_path: Path, target_path: Path) -> bool:
        """
        Create a symbolic link from source to target
        
        Args:
            source_path: Source path in /share/ directory
            target_path: Target path in project directory
            
        Returns:
            True if symlink was created successfully, False otherwise
        """
        try:
            # Ensure parent directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create the symbolic link
            target_path.symlink_to(source_path)
            
            self.logger.info(f"Created symlink: {target_path} -> {source_path}")
            return True
            
        except OSError as e:
            self.logger.error(f"Failed to create symlink {target_path} -> {source_path}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error creating symlink {target_path} -> {source_path}: {e}")
            return False
    
    def remove_symlinks(self) -> None:
        """
        Remove all symbolic links created by this manager
        """
        removed_links = []
        
        for target_dir in self.target_directories:
            project_path = self.project_root / target_dir
            
            if project_path.is_symlink():
                try:
                    project_path.unlink()
                    removed_links.append(target_dir)
                    self.logger.info(f"Removed symlink: {project_path}")
                except OSError as e:
                    self.logger.error(f"Failed to remove symlink {project_path}: {e}")
        
        if removed_links:
            self.logger.info(f"Removed symlinks: {', '.join(removed_links)}")
    
    def list_symlinks(self) -> List[str]:
        """
        List all symbolic links created by this manager
        
        Returns:
            List of directory names that are symlinks
        """
        symlinks = []
        
        for target_dir in self.target_directories:
            project_path = self.project_root / target_dir
            
            if project_path.is_symlink():
                symlinks.append(target_dir)
        
        return symlinks
    
    def get_symlink_info(self) -> dict:
        """
        Get information about all symlinks
        
        Returns:
            Dictionary with symlink information
        """
        info = {
            "project_root": str(self.project_root),
            "share_directory": str(self.share_directory),
            "symlinks": {},
            "existing_directories": {},
            "missing_in_share": {}
        }
        
        for target_dir in self.target_directories:
            share_path = self.share_directory / target_dir
            project_path = self.project_root / target_dir
            
            if project_path.is_symlink():
                info["symlinks"][target_dir] = {
                    "target": str(project_path),
                    "source": str(project_path.resolve()),
                    "exists": project_path.exists()
                }
            elif project_path.exists():
                info["existing_directories"][target_dir] = str(project_path)
            else:
                info["missing_in_share"][target_dir] = str(share_path)
        
        return info
    
    def _create_deep_symlinks(self) -> List[str]:
        """
        Create symlinks for files and subdirectories within the target directories
        This handles cases like /share/models/diffusion_models/file.safetensors
        
        Returns:
            List of created deep symlinks
        """
        deep_links = []
        
        for target_dir in self.target_directories:
            share_base = self.share_directory / target_dir
            project_base = self.project_root / target_dir
            
            if not share_base.exists():
                continue
                
            # If the target directory is already a symlink, skip deep linking
            if project_base.is_symlink():
                self.logger.debug(f"Skipping deep linking for {target_dir} (already a symlink)")
                continue
                
            # If the target directory doesn't exist, create it first
            if not project_base.exists():
                project_base.mkdir(parents=True, exist_ok=True)
            
            # Recursively scan and create symlinks for files and subdirectories
            deep_links.extend(self._scan_and_link_directory(share_base, project_base))
        
        return deep_links
    
    def _scan_and_link_directory(self, share_path: Path, project_path: Path) -> List[str]:
        """
        Recursively scan a directory and create symlinks for files and subdirectories
        Prioritizes individual files over directory symlinks
        
        Args:
            share_path: Source directory in /share/
            project_path: Target directory in project
            
        Returns:
            List of created symlinks
        """
        created_links = []
        
        try:
            # First, collect all items
            items = list(share_path.iterdir())
            
            # Separate files and directories
            files = [item for item in items if item.is_file()]
            directories = [item for item in items if item.is_dir()]
            
            # Process files first (higher priority)
            for file_item in files:
                share_item = share_path / file_item.name
                project_item = project_path / file_item.name
                
                # Skip if target already exists
                if project_item.exists():
                    self.logger.debug(f"Skipping {project_item} (already exists)")
                    continue
                
                # Create symlink for the file
                if self._create_symlink(share_item, project_item):
                    created_links.append(str(project_item.relative_to(self.project_root)))
                    self.logger.debug(f"Created file symlink: {project_item} -> {share_item}")
                else:
                    self.logger.debug(f"Failed to create symlink for {project_item}")
            
            # Then process directories
            for dir_item in directories:
                share_item = share_path / dir_item.name
                project_item = project_path / dir_item.name
                
                # Skip if target already exists
                if project_item.exists():
                    self.logger.debug(f"Skipping {project_item} (already exists)")
                    continue
                
                # Check if directory has files that should be linked individually
                has_files = any(item.is_file() for item in share_item.iterdir())
                
                if has_files:
                    # Create directory and link files individually
                    project_item.mkdir(parents=True, exist_ok=True)
                    created_links.extend(self._scan_and_link_directory(share_item, project_item))
                else:
                    # Create directory symlink
                    if self._create_symlink(share_item, project_item):
                        created_links.append(str(project_item.relative_to(self.project_root)))
                        self.logger.debug(f"Created directory symlink: {project_item} -> {share_item}")
                    else:
                        self.logger.debug(f"Failed to create symlink for {project_item}")
        
        except PermissionError as e:
            self.logger.warning(f"Permission denied scanning {share_path}: {e}")
        except Exception as e:
            self.logger.error(f"Error scanning {share_path}: {e}")
        
        return created_links


def setup_share_symlinks(project_root: str, share_directory: str = "/share") -> None:
    """
    Convenience function to set up symlinks from /share/ directory
    
    Args:
        project_root: Path to ComfyUI project root directory
        share_directory: Path to the share directory (default: /share)
    """
    manager = SymlinkManager(project_root, share_directory)
    manager.create_symlinks()
