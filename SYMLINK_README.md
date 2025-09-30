# ComfyUI Share Directory Symlink Feature

This feature automatically creates symbolic links from `/share/` directory to ComfyUI project directories during startup.

## Overview

The symlink manager scans the `/share/` directory for folders that match ComfyUI project directories and creates symbolic links to them. This allows you to:

- Share models between multiple ComfyUI instances
- Use centralized storage for custom nodes
- Maintain shared input/output directories

## Supported Directories

The following directories are automatically linked if they exist in `/share/`:

- `models` - Model files (checkpoints, LoRA, VAE, etc.)
- `custom_nodes` - Custom node extensions
- `input` - Input images and files
- `output` - Generated outputs
- `user` - User-specific data

## How It Works

1. **Startup Detection**: During ComfyUI startup, the system checks for `/share/` directory
2. **Directory Matching**: Looks for directories in `/share/` that match ComfyUI project structure
3. **Symlink Creation**: Creates symbolic links from `/share/` to project directories
4. **Skip Existing**: If a directory already exists in the project, it's skipped

## Example Directory Structure

The symlink manager supports both directory-level and file-level symlinks:

### Directory-level symlinks (when no files exist in subdirectories)
```
/share/
├── models/
│   ├── checkpoints/
│   ├── loras/
│   └── vae/
├── custom_nodes/
│   └── my_custom_node/
└── input/
    └── images/

/root/haoyc/ComfyUI/
├── models -> /share/models
├── custom_nodes -> /share/custom_nodes
└── input -> /share/input
```

### File-level symlinks (when files exist in subdirectories)
```
/share/
├── models/
│   ├── diffusion_models/
│   │   └── tmp_model.safetensors
│   ├── checkpoints/
│   │   └── checkpoint.ckpt
│   └── loras/
│       └── lora.safetensors
└── custom_nodes/
    └── my_node/
        ├── __init__.py
        └── node.py

/root/haoyc/ComfyUI/
├── models/
│   ├── diffusion_models/
│   │   └── tmp_model.safetensors -> /share/models/diffusion_models/tmp_model.safetensors
│   ├── checkpoints/
│   │   └── checkpoint.ckpt -> /share/models/checkpoints/checkpoint.ckpt
│   └── loras/
│       └── lora.safetensors -> /share/models/loras/lora.safetensors
└── custom_nodes/
    └── my_node/
        ├── __init__.py -> /share/custom_nodes/my_node/__init__.py
        └── node.py -> /share/custom_nodes/my_node/node.py
```

## Usage

The feature is automatically enabled when ComfyUI starts. No additional configuration is required.

### Manual Control

You can also use the symlink manager programmatically:

```python
from utils.symlink_manager import SymlinkManager

# Create manager
manager = SymlinkManager("/path/to/comfyui", "/share")

# Create symlinks
manager.create_symlinks()

# List existing symlinks
symlinks = manager.list_symlinks()
print(f"Active symlinks: {symlinks}")

# Get detailed info
info = manager.get_symlink_info()
print(info)

# Remove symlinks
manager.remove_symlinks()
```

## Testing

Run the test script to verify functionality:

```bash
python test_symlink.py
```

## Logging

The symlink manager provides detailed logging:

- **INFO**: Successful symlink creation
- **WARNING**: Missing share directory
- **DEBUG**: Skipped directories and detailed operations

## Error Handling

- Missing `/share/` directory: Logged as warning, startup continues
- Permission errors: Logged as error, startup continues
- Existing directories: Skipped automatically
- Invalid symlinks: Removed and recreated if possible

## Security Considerations

- Only creates symlinks for predefined directory names
- Skips existing directories to prevent data loss
- Uses absolute paths to prevent symlink attacks
- Validates source directories exist before linking

## Troubleshooting

### Symlinks Not Created

1. Check if `/share/` directory exists
2. Verify directory names match exactly (case-sensitive)
3. Check file permissions
4. Review startup logs for error messages

### Existing Directories

If you have existing directories that you want to replace with symlinks:

1. Backup your data
2. Remove the existing directory
3. Restart ComfyUI

### Permission Issues

Ensure ComfyUI has write permissions to create symlinks:

```bash
# Check permissions
ls -la /share/
ls -la /root/haoyc/ComfyUI/

# Fix permissions if needed
chmod 755 /share/
chown -R $(whoami):$(whoami) /share/
```
