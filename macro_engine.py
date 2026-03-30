"""
Macro Engine - Execute keyboard macros using pynput.
Supports key combinations, media keys, and custom sequences.
"""

from pynput.keyboard import Controller, Key
import time
from typing import List, Dict, Any


class MacroEngine:
    """Executes keyboard macros."""
    
    # Mapping of common key names to pynput Key objects
    SPECIAL_KEYS = {
        'win': Key.cmd,
        'windows': Key.cmd,
        'cmd': Key.cmd,
        'ctrl': Key.ctrl,
        'control': Key.ctrl,
        'alt': Key.alt,
        'shift': Key.shift,
        'enter': Key.enter,
        'tab': Key.tab,
        'space': Key.space,
        'backspace': Key.backspace,
        'delete': Key.delete,
        'escape': Key.esc,
        'esc': Key.esc,
        'up': Key.up,
        'down': Key.down,
        'left': Key.left,
        'right': Key.right,
        'f1': Key.f1,
        'f2': Key.f2,
        'f3': Key.f3,
        'f4': Key.f4,
        'f5': Key.f5,
        'f6': Key.f6,
        'f7': Key.f7,
        'f8': Key.f8,
        'f9': Key.f9,
        'f10': Key.f10,
        'f11': Key.f11,
        'f12': Key.f12,
        # Media keys (these may not work on all systems)
        'media_volume_mute': None,  # Handled separately
        'media_volume_up': None,
        'media_volume_down': None,
        'media_play_pause': None,
        'media_next': None,
        'media_prev': None,
    }
    
    def __init__(self):
        self.keyboard = Controller()
        self._last_gesture = None
        self._cooldown = 0.5  # seconds between same gesture triggers
        self._last_trigger_time = 0
    
    def execute(self, macro_config: Dict[str, Any]) -> bool:
        """
        Execute a macro from its configuration.
        
        Args:
            macro_config: Dict with 'action' and action-specific parameters
            
        Returns:
            bool: True if executed successfully
        """
        action = macro_config.get('action')
        
        if action == 'key_combo':
            keys = macro_config.get('keys', [])
            return self.execute_key_combo(keys)
        elif action == 'key_press':
            key = macro_config.get('key')
            return self.execute_key_press(key)
        elif action == 'text':
            text = macro_config.get('text', '')
            return self.execute_text(text)
        elif action == 'sequence':
            steps = macro_config.get('steps', [])
            delay = macro_config.get('delay', 0.1)
            return self.execute_sequence(steps, delay)
        
        return False
    
    def execute_key_combo(self, keys: List[str]) -> bool:
        """
        Execute a keyboard combination (e.g., Ctrl+C).
        
        Args:
            keys: List of key names to press together
        """
        if not keys:
            return False
        
        # Check for media keys - handle separately
        media_keys = [k for k in keys if k.startswith('media_')]
        if media_keys:
            for mk in media_keys:
                simulate_media_key(mk)
            return True
        
        # Separate modifier keys from regular keys
        modifiers = []
        regular_keys = []
        
        for key_name in keys:
            key = self._parse_key(key_name)
            if key in (Key.ctrl, Key.alt, Key.shift, Key.cmd):
                modifiers.append(key)
            else:
                regular_keys.append(key)
        
        # Press all modifiers
        for modifier in modifiers:
            self.keyboard.press(modifier)
        
        # Press regular keys
        for key in regular_keys:
            if isinstance(key, str):
                self.keyboard.tap(key)
            else:
                self.keyboard.press(key)
                self.keyboard.release(key)
        
        # Release modifiers in reverse order
        for modifier in reversed(modifiers):
            self.keyboard.release(modifier)
        
        return True
    
    def execute_key_press(self, key_name: str) -> bool:
        """Execute a single key press."""
        if not key_name:
            return False
        
        key = self._parse_key(key_name)
        
        if isinstance(key, str):
            self.keyboard.tap(key)
        else:
            self.keyboard.press(key)
            self.keyboard.release(key)
        
        return True
    
    def execute_text(self, text: str) -> bool:
        """Type out text."""
        if not text:
            return False
        
        self.keyboard.type(text)
        return True
    
    def execute_sequence(self, steps: List[Dict], delay: float = 0.1) -> bool:
        """
        Execute a sequence of macro steps.
        
        Args:
            steps: List of macro configurations
            delay: Delay between steps in seconds
        """
        for step in steps:
            self.execute(step)
            time.sleep(delay)
        return True
    
    def _parse_key(self, key_name: str):
        """
        Parse a key name string to pynput key.
        
        Args:
            key_name: Name of the key
            
        Returns:
            pynput Key object or character string
        """
        key_name = key_name.lower().strip()
        
        # Check special keys
        if key_name in self.SPECIAL_KEYS:
            special = self.SPECIAL_KEYS[key_name]
            if special is not None:
                return special
        
        # Media keys need special handling via keyboard simulation
        if key_name.startswith('media_'):
            return key_name  # Handle separately
        
        # Single character
        if len(key_name) == 1:
            return key_name
        
        # Try to find in special keys
        return Key[key_name] if hasattr(Key, key_name) else key_name
    
    def execute_with_cooldown(self, gesture: str, macro_config: Dict[str, Any], 
                              force: bool = False) -> bool:
        """
        Execute a macro with gesture-based cooldown.
        
        Args:
            gesture: Name of the triggering gesture
            macro_config: Macro configuration
            force: Ignore cooldown
            
        Returns:
            bool: True if executed
        """
        current_time = time.time()
        
        # Check cooldown for same gesture
        if not force and gesture == self._last_gesture:
            if current_time - self._last_trigger_time < self._cooldown:
                return False
        
        self._last_gesture = gesture
        self._last_trigger_time = current_time
        
        return self.execute(macro_config)
    
    def set_cooldown(self, seconds: float):
        """Set the cooldown period between same-gesture triggers."""
        self._cooldown = max(0.1, seconds)


# Media key simulation using Windows API
def simulate_media_key(key_name: str):
    """
    Simulate media keys using keyboard module (requires admin on some systems).
    
    Args:
        key_name: Media key name (media_volume_mute, etc.)
    """
    try:
        import ctypes
        import time
        
        # Virtual key codes for media keys
        media_keys = {
            'media_volume_mute': 0xAD,
            'media_volume_up': 0xAF,
            'media_volume_down': 0xAE,
            'media_play_pause': 0xB3,
            'media_next': 0xB0,
            'media_prev': 0xB1,
        }
        
        vk_code = media_keys.get(key_name)
        if vk_code:
            # Simulate key press using keyboard event
            ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
            time.sleep(0.1)
            ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)
            return True
    except Exception as e:
        print(f"Media key simulation failed: {e}")
    
    return False


if __name__ == '__main__':
    # Test the macro engine
    engine = MacroEngine()
    
    print("Testing macro engine...")
    print("Press Ctrl+C to stop")
    
    # Test various macros
    test_macros = [
        {'action': 'key_combo', 'keys': ['ctrl', 'c']},
        {'action': 'key_combo', 'keys': ['win', 'd']},
        {'action': 'text', 'text': 'Hello from GestureMacro!'},
    ]
    
    for macro in test_macros:
        print(f"Executing: {macro}")
        engine.execute(macro)
        time.sleep(1)
