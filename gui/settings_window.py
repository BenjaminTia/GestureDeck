"""
Settings Window - PyQt6 GUI for configuring gesture macros.
"""

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QPushButton, QLineEdit,
    QComboBox, QDialog, QDialogButtonBox, QGroupBox, QFormLayout,
    QMessageBox, QSplitter, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

import sys
from typing import Dict, Any, Optional, List


class MacroEditorDialog(QDialog):
    """Dialog for editing a macro configuration."""
    
    def __init__(self, macro_config: Dict[str, Any] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Macro")
        self.setMinimumWidth(400)
        
        self.action_combo = None
        self.keys_input = None
        self.text_input = None
        self.macro_config = macro_config or {'action': 'key_combo', 'keys': []}
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Action type selector
        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("Action Type:"))
        self.action_combo = QComboBox()
        self.action_combo.addItems(['key_combo', 'text'])
        self.action_combo.currentTextChanged.connect(self._on_action_changed)
        action_layout.addWidget(self.action_combo)
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        # Key combination input
        self.keys_group = QGroupBox("Key Combination")
        keys_layout = QVBoxLayout(self.keys_group)
        
        keys_hint = QLabel("Enter keys separated by + (e.g., ctrl+c or alt+tab)")
        keys_hint.setWordWrap(True)
        keys_layout.addWidget(keys_hint)
        
        self.keys_input = QLineEdit()
        self.keys_input.setPlaceholderText("ctrl+c")
        keys_layout.addWidget(self.keys_input)
        
        # Common shortcuts
        shortcuts_label = QLabel("Common shortcuts:")
        keys_layout.addWidget(shortcuts_label)
        
        shortcuts = QHBoxLayout()
        self.shortcut_buttons = []
        common_shortcuts = [
            "Ctrl+C", "Ctrl+V", "Ctrl+X", "Ctrl+Z",
            "Alt+Tab", "Win+D", "Ctrl+Shift+Esc"
        ]
        for shortcut in common_shortcuts:
            btn = QPushButton(shortcut)
            btn.clicked.connect(lambda checked, s=shortcut: self._insert_shortcut(s))
            self.shortcut_buttons.append(btn)
            shortcuts.addWidget(btn)
        keys_layout.addLayout(shortcuts)
        
        layout.addWidget(self.keys_group)
        
        # Text input (for text action)
        self.text_group = QGroupBox("Text to Type")
        text_layout = QVBoxLayout(self.text_group)
        self.text_input = QTextEdit()
        self.text_input.setMaximumHeight(100)
        self.text_input.setPlaceholderText("Hello, World!")
        text_layout.addWidget(self.text_input)
        layout.addWidget(self.text_group)
        
        # Initially hide text group
        self.text_group.setVisible(False)
        
        # Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        # Load existing config
        self._load_config()
        
    def _on_action_changed(self, action: str):
        """Show/hide relevant input fields."""
        is_key_combo = action == 'key_combo'
        self.keys_group.setVisible(is_key_combo)
        self.text_group.setVisible(not is_key_combo)
        
    def _insert_shortcut(self, shortcut: str):
        """Insert a common shortcut into the input."""
        self.keys_input.setText(shortcut.replace('+', '+').lower())
        
    def _load_config(self):
        """Load existing macro config into UI."""
        action = self.macro_config.get('action', 'key_combo')
        self.action_combo.setCurrentText(action)
        
        if action == 'key_combo':
            keys = self.macro_config.get('keys', [])
            self.keys_input.setText('+'.join(keys))
        elif action == 'text':
            text = self.macro_config.get('text', '')
            self.text_input.setPlainText(text)
            
    def get_macro_config(self) -> Dict[str, Any]:
        """Get the configured macro."""
        action = self.action_combo.currentText()
        
        if action == 'key_combo':
            keys_text = self.keys_input.text().strip()
            keys = [k.strip().lower() for k in keys_text.split('+') if k.strip()]
            return {'action': 'key_combo', 'keys': keys}
        elif action == 'text':
            text = self.text_input.toPlainText().strip()
            return {'action': 'text', 'text': text}
        
        return {'action': 'key_combo', 'keys': []}


class GestureMacroSettings(QMainWindow):
    """Main settings window for GestureMacro."""
    
    profile_changed = pyqtSignal(str)  # Emitted when profile changes
    macro_updated = pyqtSignal(str, dict)  # Emitted when a macro is updated
    
    def __init__(self, profile_manager):
        super().__init__()
        self.profile_manager = profile_manager
        self.gesture_list = None
        self.macro_labels = {}
        
        self._setup_ui()
        self._load_gestures()
        
    def _setup_ui(self):
        self.setWindowTitle("GestureMacro Settings")
        self.setMinimumSize(800, 600)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Header
        header = QLabel("Gesture Macro Configuration")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        main_layout.addWidget(header)
        
        # Profile selector
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("Profile:"))
        self.profile_combo = QComboBox()
        self._refresh_profiles()
        self.profile_combo.currentTextChanged.connect(self._on_profile_changed)
        profile_layout.addWidget(self.profile_combo)
        
        self.new_profile_btn = QPushButton("New")
        self.new_profile_btn.clicked.connect(self._new_profile)
        profile_layout.addWidget(self.new_profile_btn)
        
        self.save_profile_btn = QPushButton("Save")
        self.save_profile_btn.clicked.connect(self._save_profile)
        profile_layout.addWidget(self.save_profile_btn)
        
        profile_layout.addStretch()
        main_layout.addLayout(profile_layout)
        
        # Splitter for gesture list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Gesture list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_layout.addWidget(QLabel("Gestures:"))
        self.gesture_list = QListWidget()
        self.gesture_list.itemClicked.connect(self._on_gesture_selected)
        left_layout.addWidget(self.gesture_list)
        
        splitter.addWidget(left_panel)
        
        # Right panel - Macro configuration
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.config_group = QGroupBox("Macro Configuration")
        config_layout = QVBoxLayout(self.config_group)
        
        # Current gesture display
        self.gesture_name_label = QLabel("Select a gesture")
        self.gesture_name_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        config_layout.addWidget(self.gesture_name_label)
        
        # Current macro display
        macro_label = QLabel("Assigned Macro:")
        config_layout.addWidget(macro_label)
        
        self.macro_display = QLabel("None")
        self.macro_display.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }")
        self.macro_display.setWordWrap(True)
        config_layout.addWidget(self.macro_display)
        
        # Edit button
        self.edit_btn = QPushButton("Edit Macro")
        self.edit_btn.clicked.connect(self._edit_macro)
        self.edit_btn.setEnabled(False)
        config_layout.addWidget(self.edit_btn)
        
        # Clear button
        self.clear_btn = QPushButton("Clear Macro")
        self.clear_btn.clicked.connect(self._clear_macro)
        self.clear_btn.setEnabled(False)
        config_layout.addWidget(self.clear_btn)
        
        config_layout.addStretch()
        
        # Help text
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(150)
        help_text.setHtml("""
            <h4>Help</h4>
            <ul>
                <li><b>Fist:</b> All fingers curled (0 fingers)</li>
                <li><b>One-Five:</b> Finger count gestures</li>
                <li><b>Six-Ten:</b> One hand (5) + second hand finger count</li>
                <li><b>Peace:</b> Index and middle finger up</li>
                <li><b>OK:</b> Thumb and index touching in circle</li>
                <li><b>Thumbs Up:</b> Only thumb extended</li>
                <li><b>Point:</b> Only index finger pointing</li>
            </ul>
        """)
        config_layout.addWidget(help_text)
        
        right_layout.addWidget(self.config_group)
        splitter.addWidget(right_panel)
        
        # Set splitter sizes
        splitter.setSizes([250, 550])
        main_layout.addWidget(splitter)
        
        # Status bar
        self.statusBar().showMessage("Select a gesture to configure its macro")
        
        # Current selection
        self._selected_gesture = None
        
    def _refresh_profiles(self):
        """Refresh the profile combo box."""
        self.profile_combo.clear()
        profiles = self.profile_manager.list_profiles()
        self.profile_combo.addItems(profiles)
        
        # Select current profile
        current = self.profile_manager.get_current_profile_name()
        if current and current in profiles:
            self.profile_combo.setCurrentText(current)
            
    def _load_gestures(self):
        """Load all gestures into the list."""
        self.gesture_list.clear()
        gestures = self.profile_manager.get_all_gestures()
        
        for gesture in gestures:
            item = QListWidgetItem(gesture.replace('_', ' ').title())
            item.setData(Qt.ItemDataRole.UserRole, gesture)
            self.gesture_list.addItem(item)
            
    def _on_profile_changed(self, profile_name: str):
        """Handle profile selection change."""
        self.profile_manager.load_profile(profile_name)
        self._load_gestures()
        self._clear_selection()
        self.profile_changed.emit(profile_name)
        self.statusBar().showMessage(f"Loaded profile: {profile_name}")
        
    def _new_profile(self):
        """Create a new profile."""
        name, ok = QLineEdit.getText(
            self, "New Profile", "Enter profile name:"
        )
        if ok and name:
            # Create from default
            default = self.profile_manager.create_default_profile()
            default['name'] = name
            self.profile_manager.save_profile(default, name)
            self._refresh_profiles()
            self.profile_combo.setCurrentText(name.lower().replace(' ', '_'))
            self.statusBar().showMessage(f"Created profile: {name}")
            
    def _save_profile(self):
        """Save current profile."""
        profile_name = self.profile_manager.get_current_profile_name()
        if profile_name:
            self.profile_manager.save_profile(
                self.profile_manager._current_profile,
                profile_name
            )
            self.statusBar().showMessage(f"Saved profile: {profile_name}")
            QMessageBox.information(self, "Saved", f"Profile '{profile_name}' saved successfully!")
            
    def _on_gesture_selected(self, item: QListWidgetItem):
        """Handle gesture selection."""
        gesture = item.data(Qt.ItemDataRole.UserRole)
        self._selected_gesture = gesture
        
        self.gesture_name_label.setText(gesture.replace('_', ' ').title())
        self.edit_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        
        # Load current macro
        macro = self.profile_manager.get_gesture_macro(gesture)
        self._update_macro_display(macro)
        
        self.statusBar().showMessage(f"Selected gesture: {gesture}")
        
    def _update_macro_display(self, macro: Optional[Dict[str, Any]]):
        """Update the macro display label."""
        if macro is None:
            self.macro_display.setText("No macro assigned")
            return
        
        action = macro.get('action', 'unknown')
        
        if action == 'key_combo':
            keys = macro.get('keys', [])
            self.macro_display.setText(f"Key Combination: {' + '.join(keys)}")
        elif action == 'text':
            text = macro.get('text', '')
            preview = text[:50] + "..." if len(text) > 50 else text
            self.macro_display.setText(f"Type Text: \"{preview}\"")
        else:
            self.macro_display.setText(f"Action: {action}")
            
    def _edit_macro(self):
        """Open macro editor dialog."""
        if not self._selected_gesture:
            return
        
        current_macro = self.profile_manager.get_gesture_macro(self._selected_gesture)
        
        dialog = MacroEditorDialog(current_macro, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_macro = dialog.get_macro_config()
            self.profile_manager.set_gesture_macro(self._selected_gesture, new_macro)
            self._update_macro_display(new_macro)
            self.macro_updated.emit(self._selected_gesture, new_macro)
            self.statusBar().showMessage(f"Updated macro for: {self._selected_gesture}")
            
    def _clear_macro(self):
        """Clear the macro for selected gesture."""
        if not self._selected_gesture:
            return
        
        reply = QMessageBox.question(
            self, "Clear Macro",
            f"Clear macro for '{self._selected_gesture}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.profile_manager.set_gesture_macro(self._selected_gesture, None)
            self._update_macro_display(None)
            self.statusBar().showMessage(f"Cleared macro for: {self._selected_gesture}")
            
    def _clear_selection(self):
        """Clear the current selection."""
        self._selected_gesture = None
        self.gesture_name_label.setText("Select a gesture")
        self.macro_display.setText("None")
        self.edit_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)


if __name__ == '__main__':
    # Test the settings window
    from profile_manager import ProfileManager
    
    app = QApplication(sys.argv)
    
    manager = ProfileManager()
    manager.load_profile("default")
    
    window = GestureMacroSettings(manager)
    window.show()
    
    sys.exit(app.exec())
