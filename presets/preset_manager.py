"""
Preset Manager Module

This module handles the management of exposure bracket presets,
including saving, loading, importing, and exporting presets.
"""

import os
import json
import uuid
import shutil
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PresetManager:
    """Manager for exposure bracket presets"""
    
    def __init__(self, preset_dir="presets"):
        """
        Initialize the preset manager
        
        Args:
            preset_dir: Directory to store presets
        """
        self.preset_dir = preset_dir
        self.default_dir = os.path.join(preset_dir, "default_presets")
        self.user_dir = os.path.join(preset_dir, "user_presets")
        
        # Create directories if they don't exist
        for directory in [self.preset_dir, self.default_dir, self.user_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"Created directory: {directory}")
        
        # Load default presets
        self._load_default_presets()
        
        logger.info("Preset manager initialized")
    
    def _load_default_presets(self):
        """Load default presets if none exist"""
        # Check if default presets directory is empty
        if not os.listdir(self.default_dir):
            logger.info("Creating default presets")
            self._create_default_presets()
    
    def _create_default_presets(self):
        """Create default presets"""
        default_presets = [
            {
                "id": "full_moon",
                "name": "Full Moon HDR",
                "description": "High dynamic range capture for full moon",
                "capture_mode": "standard",
                "brackets": [
                    {
                        "name": "Highlights",
                        "iso": 100,
                        "aperture": 11,
                        "shutter_speed": "1/500",
                        "frames": 40
                    },
                    {
                        "name": "Normal",
                        "iso": 100,
                        "aperture": 8.0,
                        "shutter_speed": "1/250",
                        "frames": 40
                    },
                    {
                        "name": "Shadows",
                        "iso": 100,
                        "aperture": 5.6,
                        "shutter_speed": "1/125",
                        "frames": 20
                    }
                ]
            },
            {
                "id": "landscape_hdr",
                "name": "Landscape HDR",
                "description": "3-bracket HDR for landscapes",
                "capture_mode": "standard",
                "brackets": [
                    {
                        "name": "Underexposed",
                        "iso": 100,
                        "aperture": 11,
                        "shutter_speed": "1/250",
                        "frames": 3
                    },
                    {
                        "name": "Normal",
                        "iso": 100,
                        "aperture": 11,
                        "shutter_speed": "1/60",
                        "frames": 3
                    },
                    {
                        "name": "Overexposed",
                        "iso": 100,
                        "aperture": 11,
                        "shutter_speed": "1/15",
                        "frames": 3
                    }
                ]
            },
            {
                "id": "quick_stack",
                "name": "Quick Stack",
                "description": "Single exposure, 50 frames for stacking",
                "capture_mode": "fast",
                "brackets": [
                    {
                        "name": "Main Stack",
                        "iso": 100,
                        "aperture": 8.0,
                        "shutter_speed": "1/250",
                        "frames": 50
                    }
                ]
            },
            {
                "id": "focus_stack",
                "name": "Focus Stack",
                "description": "Focus stacking for macro photography",
                "capture_mode": "standard",
                "brackets": [
                    {
                        "name": "Focus Stack",
                        "iso": 100,
                        "aperture": 8.0,
                        "shutter_speed": "1/60",
                        "frames": 10
                    }
                ],
                "focus_stack": {
                    "enabled": True,
                    "steps": 10,
                    "step_size": 3
                }
            }
        ]
        
        # Save default presets
        for preset in default_presets:
            preset_path = os.path.join(self.default_dir, f"{preset['id']}.json")
            with open(preset_path, 'w') as f:
                json.dump(preset, f, indent=2)
            logger.info(f"Created default preset: {preset['name']}")
    
    def get_all_presets(self):
        """
        Get all available presets, including those in subdirectories
        
        Returns:
            list: List of preset dictionaries with folder information
        """
        presets = []
        
        # Load default presets
        default_presets = self._load_presets_from_dir(self.default_dir, 'default')
        presets.extend(default_presets)
        
        # Load user presets (including those in subdirectories)
        user_presets = self._load_presets_from_dir(self.user_dir, 'user')
        presets.extend(user_presets)
        
        # Sort by folder first, then by name
        presets.sort(key=lambda x: (x.get('folder', ''), x.get('name', '')))
        
        logger.info(f"Loaded {len(presets)} presets")
        return presets
    
    def _load_presets_from_dir(self, directory, preset_type, relative_path=''):
        """
        Recursively load presets from a directory and its subdirectories
        
        Args:
            directory: Base directory to load from
            preset_type: Type of preset ('default' or 'user')
            relative_path: Relative path from the base directory
            
        Returns:
            list: List of preset dictionaries
        """
        presets = []
        full_path = os.path.join(directory, relative_path)
        
        try:
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                
                # If it's a directory, recursively load presets from it
                if os.path.isdir(item_path):
                    subfolder_path = os.path.join(relative_path, item) if relative_path else item
                    subfolder_presets = self._load_presets_from_dir(directory, preset_type, subfolder_path)
                    presets.extend(subfolder_presets)
                
                # If it's a JSON file, load it as a preset
                elif item.endswith('.json'):
                    try:
                        with open(item_path, 'r') as f:
                            preset = json.load(f)
                            preset['type'] = preset_type
                            
                            # Add folder information
                            if relative_path:
                                preset['folder'] = relative_path
                            
                            presets.append(preset)
                    except Exception as e:
                        logger.error(f"Error loading {preset_type} preset {item_path}: {e}")
        except Exception as e:
            logger.error(f"Error accessing directory {full_path}: {e}")
        
        return presets
    
    def get_preset(self, preset_id):
        """
        Get a specific preset by ID
        
        Args:
            preset_id: ID of the preset
        
        Returns:
            dict: Preset dictionary or None if not found
        """
        # First try to find the preset in the default and user directories
        default_path = os.path.join(self.default_dir, f"{preset_id}.json")
        if os.path.exists(default_path):
            try:
                with open(default_path, 'r') as f:
                    preset = json.load(f)
                    preset['type'] = 'default'
                    return preset
            except Exception as e:
                logger.error(f"Error loading default preset {preset_id}: {e}")
        
        user_path = os.path.join(self.user_dir, f"{preset_id}.json")
        if os.path.exists(user_path):
            try:
                with open(user_path, 'r') as f:
                    preset = json.load(f)
                    preset['type'] = 'user'
                    return preset
            except Exception as e:
                logger.error(f"Error loading user preset {preset_id}: {e}")
        
        # If not found, search recursively in subdirectories
        preset = self._find_preset_in_subdirs(self.default_dir, preset_id, 'default')
        if preset:
            return preset
            
        preset = self._find_preset_in_subdirs(self.user_dir, preset_id, 'user')
        if preset:
            return preset
        
        logger.warning(f"Preset {preset_id} not found")
        return None
    
    def _find_preset_in_subdirs(self, base_dir, preset_id, preset_type, relative_path=''):
        """
        Recursively search for a preset in subdirectories
        
        Args:
            base_dir: Base directory to search in
            preset_id: ID of the preset to find
            preset_type: Type of preset ('default' or 'user')
            relative_path: Relative path from the base directory
            
        Returns:
            dict: Preset dictionary or None if not found
        """
        full_path = os.path.join(base_dir, relative_path)
        
        try:
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                
                # If it's a directory, search recursively
                if os.path.isdir(item_path):
                    subfolder_path = os.path.join(relative_path, item) if relative_path else item
                    preset = self._find_preset_in_subdirs(base_dir, preset_id, preset_type, subfolder_path)
                    if preset:
                        return preset
                
                # If it's a JSON file with the matching ID, load it
                elif item == f"{preset_id}.json":
                    try:
                        with open(item_path, 'r') as f:
                            preset = json.load(f)
                            preset['type'] = preset_type
                            
                            # Add folder information
                            if relative_path:
                                preset['folder'] = relative_path
                            
                            return preset
                    except Exception as e:
                        logger.error(f"Error loading {preset_type} preset {item_path}: {e}")
        except Exception as e:
            logger.error(f"Error accessing directory {full_path}: {e}")
        
        return None
    
    def save_preset(self, preset_data):
        """
        Save a preset
        
        Args:
            preset_data: Dictionary with preset data
        
        Returns:
            str: Preset ID
        """
        try:
            # Generate ID if not provided
            if 'id' not in preset_data:
                preset_data['id'] = str(uuid.uuid4())
            
            # Ensure required fields
            if 'name' not in preset_data:
                preset_data['name'] = f"Preset {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if 'brackets' not in preset_data or not preset_data['brackets']:
                raise ValueError("Preset must contain at least one bracket")
            
            # Determine save directory (handle folders)
            save_dir = self.user_dir
            if 'folder' in preset_data and preset_data['folder']:
                folder_path = os.path.join(self.user_dir, preset_data['folder'])
                # Create folder if it doesn't exist
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                save_dir = folder_path
            
            # Save to appropriate directory
            preset_path = os.path.join(save_dir, f"{preset_data['id']}.json")
            with open(preset_path, 'w') as f:
                json.dump(preset_data, f, indent=2)
            
            logger.info(f"Saved preset: {preset_data['name']} ({preset_data['id']})")
            return preset_data['id']
            
        except Exception as e:
            logger.error(f"Error saving preset: {e}")
            raise
    
    def delete_preset(self, preset_id):
        """
        Delete a preset
        
        Args:
            preset_id: ID of the preset to delete
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if it's a default preset
            default_path = os.path.join(self.default_dir, f"{preset_id}.json")
            if os.path.exists(default_path):
                logger.warning(f"Cannot delete default preset: {preset_id}")
                return False
            
            # Check if it's a user preset in the root directory
            user_path = os.path.join(self.user_dir, f"{preset_id}.json")
            if os.path.exists(user_path):
                os.remove(user_path)
                logger.info(f"Deleted preset: {preset_id}")
                return True
            
            # If not found in the root directory, search in subdirectories
            preset = self._find_preset_in_subdirs(self.user_dir, preset_id, 'user')
            if preset and 'folder' in preset:
                # Construct the path to the preset file
                folder_path = os.path.join(self.user_dir, preset['folder'])
                preset_path = os.path.join(folder_path, f"{preset_id}.json")
                
                if os.path.exists(preset_path):
                    os.remove(preset_path)
                    logger.info(f"Deleted preset: {preset_id} from folder: {preset['folder']}")
                    return True
            
            logger.warning(f"Preset not found: {preset_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error deleting preset {preset_id}: {e}")
            return False
    
    def import_preset(self, preset_data):
        """
        Import a preset from external data
        
        Args:
            preset_data: Dictionary with preset data
        
        Returns:
            str: Preset ID
        """
        try:
            # Validate preset data
            if 'brackets' not in preset_data or not preset_data['brackets']:
                raise ValueError("Invalid preset data: missing brackets")
            
            # Generate new ID to avoid conflicts
            preset_data['id'] = str(uuid.uuid4())
            
            # Add import timestamp
            preset_data['imported'] = datetime.now().isoformat()
            
            # Save as user preset
            return self.save_preset(preset_data)
            
        except Exception as e:
            logger.error(f"Error importing preset: {e}")
            raise
    
    def export_preset(self, preset_id):
        """
        Export a preset to a file
        
        Args:
            preset_id: ID of the preset to export
        
        Returns:
            str: Path to exported file or None if failed
        """
        try:
            # Get preset
            preset = self.get_preset(preset_id)
            if not preset:
                logger.warning(f"Preset not found: {preset_id}")
                return None
            
            # Create exports directory if it doesn't exist
            exports_dir = os.path.join(self.preset_dir, "exports")
            if not os.path.exists(exports_dir):
                os.makedirs(exports_dir)
            
            # Create export filename
            safe_name = preset.get('name', 'preset').replace(' ', '_').lower()
            export_path = os.path.join(exports_dir, f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            # Save to file
            with open(export_path, 'w') as f:
                json.dump(preset, f, indent=2)
            
            logger.info(f"Exported preset {preset_id} to {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"Error exporting preset {preset_id}: {e}")
            return None
    
    def duplicate_preset(self, preset_id):
        """
        Duplicate a preset
        
        Args:
            preset_id: ID of the preset to duplicate
        
        Returns:
            str: New preset ID or None if failed
        """
        try:
            # Get preset
            preset = self.get_preset(preset_id)
            if not preset:
                logger.warning(f"Preset not found: {preset_id}")
                return None
            
            # Create a copy
            new_preset = preset.copy()
            new_preset.pop('id', None)
            new_preset.pop('type', None)
            new_preset['name'] = f"Copy of {preset.get('name', 'Preset')}"
            
            # Save as new preset
            return self.save_preset(new_preset)
            
        except Exception as e:
            logger.error(f"Error duplicating preset {preset_id}: {e}")
            return None


# Simple test function
def test():
    """Test the preset manager"""
    manager = PresetManager()
    
    # Get all presets
    print("Available presets:")
    presets = manager.get_all_presets()
    for preset in presets:
        print(f"  {preset['name']} ({preset['id']}) - {preset['description']}")
    
    # Create a test preset
    test_preset = {
        "name": "Test Preset",
        "description": "Created for testing",
        "capture_mode": "standard",
        "brackets": [
            {
                "name": "Test Bracket",
                "iso": 100,
                "aperture": 8.0,
                "shutter_speed": "1/125",
                "frames": 5
            }
        ]
    }
    
    # Save preset
    print("\nSaving test preset...")
    preset_id = manager.save_preset(test_preset)
    print(f"Saved preset ID: {preset_id}")
    
    # Get the preset
    print("\nRetrieving saved preset...")
    saved_preset = manager.get_preset(preset_id)
    print(f"Retrieved: {saved_preset['name']} ({saved_preset['id']})")
    
    # Export the preset
    print("\nExporting preset...")
    export_path = manager.export_preset(preset_id)
    print(f"Exported to: {export_path}")
    
    # Delete the preset
    print("\nDeleting preset...")
    result = manager.delete_preset(preset_id)
    print(f"Delete result: {result}")


if __name__ == "__main__":
    test()