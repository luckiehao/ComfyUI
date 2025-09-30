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
        Incremental sync: Create directories and symlinks for all files that don't exist in ComfyUI
        """
        if not self.share_directory.exists():
            self.logger.warning(f"Share directory {self.share_directory} does not exist, skipping symlink creation")
            return
        
        self.logger.info(f"Starting incremental sync from {self.share_directory} to {self.project_root}")
        
        created_links = []
        created_directories = []
        skipped_items = []
        
        for target_dir in self.target_directories:
            share_path = self.share_directory / target_dir
            project_path = self.project_root / target_dir
            
            if not share_path.exists():
                self.logger.debug(f"Source {share_path} does not exist in share directory")
                skipped_items.append(target_dir)
                continue
            
            # Recursively sync the directory structure
            sync_result = self._sync_directory_recursive(share_path, project_path)
            created_links.extend(sync_result['links'])
            created_directories.extend(sync_result['directories'])
        
        if created_directories:
            self.logger.info(f"Successfully created directories: {', '.join(created_directories)}")
        
        if created_links:
            self.logger.info(f"Successfully created symlinks for: {', '.join(created_links)}")
        
        if skipped_items:
            self.logger.info(f"Skipped items (not found in share): {', '.join(skipped_items)}")
    
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
    
    def _sync_directory_recursive(self, share_path: Path, project_path: Path) -> dict:
        """
        Recursively sync directory structure from share to project
        Creates directories and symlinks for all files that don't exist in project
        
        Args:
            share_path: Source directory in /share/
            project_path: Target directory in project
            
        Returns:
            Dictionary with 'links' and 'directories' lists
        """
        result = {'links': [], 'directories': []}
        
        try:
            # Ensure target directory exists
            if not project_path.exists():
                project_path.mkdir(parents=True, exist_ok=True)
                result['directories'].append(str(project_path.relative_to(self.project_root)))
                self.logger.debug(f"Created directory: {project_path}")
            
            # Process all items in the share directory
            for item in share_path.iterdir():
                share_item = share_path / item.name
                project_item = project_path / item.name
                
                if item.is_file():
                    # For files, create symlink if it doesn't exist
                    if not project_item.exists():
                        if self._create_symlink(share_item, project_item):
                            result['links'].append(str(project_item.relative_to(self.project_root)))
                            self.logger.debug(f"Created file symlink: {project_item} -> {share_item}")
                    else:
                        self.logger.debug(f"File {project_item} already exists, skipping")
                        
                elif item.is_dir():
                    # For directories, recursively sync
                    sub_result = self._sync_directory_recursive(share_item, project_item)
                    result['links'].extend(sub_result['links'])
                    result['directories'].extend(sub_result['directories'])
                    
        except Exception as e:
            self.logger.error(f"Error syncing directory {share_path}: {e}")
        
        return result
    
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
            deep_links.extend(self._scan_and_link_directory(share_base, project_base, 0))
        
        return deep_links
    
    def _create_deep_symlinks_for_existing_directory(self, share_path: Path, project_path: Path) -> List[str]:
        """
        Create symlinks for files and subdirectories in an existing directory
        Only creates symlinks for items that don't already exist in the project
        
        Args:
            share_path: Source directory in /share/
            project_path: Target directory in project (already exists)
            
        Returns:
            List of created symlinks
        """
        created_links = []
        
        try:
            # Recursively scan and create symlinks for new files and subdirectories
            created_links.extend(self._scan_and_link_directory(share_path, project_path, 0))
        except Exception as e:
            self.logger.error(f"Error creating deep symlinks for existing directory {project_path}: {e}")
        
        return created_links
    
    def _scan_and_link_directory(self, share_path: Path, project_path: Path, depth: int = 0) -> List[str]:
        """
        Recursively scan a directory and create symlinks for files and subdirectories
        Prioritizes individual files over directory symlinks
        
        Args:
            share_path: Source directory in /share/
            project_path: Target directory in project
            depth: Current recursion depth (0-based)
            
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
                
                # If target already exists, continue scanning for new files
                if project_item.exists():
                    self.logger.debug(f"Target {project_item} already exists, scanning for new files")
                    # Continue scanning for new files in existing directory
                    if share_item.is_dir():
                        created_links.extend(self._scan_and_link_directory(share_item, project_item, depth + 1))
                    continue
                
                # Check if directory has files that should be linked individually
                has_files = any(item.is_file() for item in share_item.iterdir())
                
                if has_files:
                    # Create directory and link files individually
                    project_item.mkdir(parents=True, exist_ok=True)
                    created_links.extend(self._scan_and_link_directory(share_item, project_item, depth + 1))
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
