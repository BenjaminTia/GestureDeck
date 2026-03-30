"""
Profile Manager - Load, save, and manage gesture macro profiles.
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path


class ProfileManager:
    """Manages gesture macro profiles."""
    
    DEFAULT_PROFILE_NAME = "Default"
    PROFILES_DIR = Path(__file__).parent / "profiles"
    
    def __init__(self):
        """Initialize profile manager."""
        self._profiles_dir = self.PROFILES_DIR
        self._profiles_dir.mkdir(exist_ok=True)
        self._current_profile = None
        self._current_profile_name = None
        
    def load_profile(self, profile_name: str = None) -> Optional[Dict[str, Any]]:
        """
        Load a profile by name.
        
        Args:
            profile_name: Name of profile to load (without .json extension)
            
        Returns:
            Profile dict or None if not found
        """
        if profile_name is None:
            profile_name = self.DEFAULT_PROFILE_NAME
        
        profile_path = self._profiles_dir / f"{profile_name}.json"
        
        if not profile_path.exists():
            return None
        
        try:
            with open(profile_path, 'r') as f:
                profile = json.load(f)
            
            self._current_profile = profile
            self._current_profile_name = profile_name
            return profile
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading profile: {e}")
            return None
    
    def save_profile(self, profile: Dict[str, Any], profile_name: str = None) -> bool:
        """
        Save a profile.
        
        Args:
            profile: Profile dict to save
            profile_name: Name for the profile
            
        Returns:
            bool: True if saved successfully
        """
        if profile_name is None:
            profile_name = profile.get('name', 'unnamed')
        
        # Sanitize filename
        profile_name = "".join(c for c in profile_name if c.isalnum() or c in (' ', '-', '_')).strip()
        profile_name = profile_name.replace(' ', '_').lower()
        
        profile_path = self._profiles_dir / f"{profile_name}.json"
        
        try:
            with open(profile_path, 'w') as f:
                json.dump(profile, f, indent=2)
            
            self._current_profile = profile
            self._current_profile_name = profile_name
            return True
        except IOError as e:
            print(f"Error saving profile: {e}")
            return False
    
    def create_default_profile(self) -> Dict[str, Any]:
        """Create a default profile with common mappings."""
        return {
            "name": "Default",
            "description": "Default gesture macro mappings",
            "gestures": {
                "fist": {"action": "key_combo", "keys": ["win", "d"]},
                "one": {"action": "key_combo", "keys": ["ctrl", "c"]},
                "two": {"action": "key_combo", "keys": ["ctrl", "v"]},
                "three": {"action": "key_combo", "keys": ["alt", "tab"]},
                "four": {"action": "key_combo", "keys": ["ctrl", "shift", "esc"]},
                "five": {"action": "key_combo", "keys": ["win", "e"]},
                "six": {"action": "key_combo", "keys": ["ctrl", "t"]},
                "seven": {"action": "key_combo", "keys": ["ctrl", "w"]},
                "eight": {"action": "key_combo", "keys": ["ctrl", "shift", "t"]},
                "nine": {"action": "key_combo", "keys": ["ctrl", "tab"]},
                "ten": {"action": "key_combo", "keys": ["win", "l"]},
                "peace": {"action": "key_combo", "keys": ["media_volume_mute"]},
                "ok": {"action": "key_combo", "keys": ["media_play_pause"]},
                "thumbs_up": {"action": "key_combo", "keys": ["media_volume_up"]},
                "point": {"action": "key_combo", "keys": ["media_volume_down"]}
            }
        }
    
    def get_gesture_macro(self, gesture_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the macro configuration for a specific gesture.
        
        Args:
            gesture_name: Name of the gesture
            
        Returns:
            Macro config dict or None
        """
        if self._current_profile is None:
            return None
        
        gestures = self._current_profile.get('gestures', {})
        return gestures.get(gesture_name)
    
    def set_gesture_macro(self, gesture_name: str, macro_config: Dict[str, Any]) -> bool:
        """
        Set or update a gesture's macro configuration.
        
        Args:
            gesture_name: Name of the gesture
            macro_config: New macro configuration
            
        Returns:
            bool: True if updated successfully
        """
        if self._current_profile is None:
            return False
        
        if 'gestures' not in self._current_profile:
            self._current_profile['gestures'] = {}
        
        self._current_profile['gestures'][gesture_name] = macro_config
        return True
    
    def list_profiles(self) -> List[str]:
        """List all available profile names."""
        profiles = []
        for f in self._profiles_dir.glob("*.json"):
            profiles.append(f.stem)
        return sorted(profiles)
    
    def delete_profile(self, profile_name: str) -> bool:
        """
        Delete a profile.
        
        Args:
            profile_name: Name of profile to delete
            
        Returns:
            bool: True if deleted successfully
        """
        profile_path = self._profiles_dir / f"{profile_name}.json"
        
        if not profile_path.exists():
            return False
        
        try:
            profile_path.unlink()
            if self._current_profile_name == profile_name:
                self._current_profile = None
                self._current_profile_name = None
            return True
        except IOError as e:
            print(f"Error deleting profile: {e}")
            return False
    
    def export_profile(self, profile_name: str, output_path: str) -> bool:
        """Export a profile to a specific file path."""
        profile = self.load_profile(profile_name)
        if profile is None:
            return False
        
        try:
            with open(output_path, 'w') as f:
                json.dump(profile, f, indent=2)
            return True
        except IOError:
            return False
    
    def import_profile(self, input_path: str, new_name: str = None) -> bool:
        """Import a profile from a file."""
        try:
            with open(input_path, 'r') as f:
                profile = json.load(f)
            
            if new_name:
                profile['name'] = new_name
            
            return self.save_profile(profile)
        except (json.JSONDecodeError, IOError):
            return False
    
    def get_current_profile_name(self) -> Optional[str]:
        """Get the name of the currently loaded profile."""
        return self._current_profile_name
    
    def get_all_gestures(self) -> List[str]:
        """Get list of all supported gesture names."""
        from gesture_detector import GestureDetector
        return GestureDetector.GESTURES.copy()


if __name__ == '__main__':
    # Test profile manager
    manager = ProfileManager()
    
    print("Available profiles:", manager.list_profiles())
    
    # Load default profile
    profile = manager.load_profile("default")
    if profile:
        print(f"Loaded profile: {profile['name']}")
        print("Gestures:", list(profile.get('gestures', {}).keys()))
    
    # Get a specific gesture macro
    macro = manager.get_gesture_macro("fist")
    print(f"Fist macro: {macro}")
