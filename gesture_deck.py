"""
GestureMacro - Simple All-in-One Version
Shows camera feed and settings in one window.
"""

import sys
import os
import cv2
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QMessageBox, QGroupBox,
    QFormLayout, QLineEdit, QTextEdit, QSplitter, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QImage, QPixmap, QFont

from gesture_detector import GestureDetector
from macro_engine import MacroEngine
from profile_manager import ProfileManager


class CameraWidget(QLabel):
    """Widget that displays camera feed with gesture overlay."""
    
    gesture_detected = pyqtSignal(str, float)
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(640, 480)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("QLabel { background-color: #1a1a1a; border-radius: 10px; }")
        
        self.detector = GestureDetector()
        self.macro_engine = MacroEngine()
        self.profile_manager = ProfileManager()
        self.profile_manager.load_profile("default")
        
        self.capture = None
        self.current_gesture = None
        self.last_trigger_time = 0
        self.last_triggered_gesture = None
        
    def start_camera(self):
        """Start camera capture."""
        self.capture = cv2.VideoCapture(0)
        if not self.capture.isOpened():
            QMessageBox.critical(self, "Error", "Could not open camera")
            return False
        return True
        
    def stop_camera(self):
        """Stop camera capture."""
        if self.capture:
            self.capture.release()
            
    def update_frame(self):
        """Capture and display a frame."""
        if not self.capture or not self.capture.isOpened():
            return
            
        ret, frame = self.capture.read()
        if not ret:
            return
            
        # Flip for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Detect gesture
        gesture, confidence, landmarks, annotated = self.detector.detect(frame)
        
        # Check for macro trigger
        macro_triggered = False
        if gesture:
            macro = self.profile_manager.get_gesture_macro(gesture)
            if macro:
                current_time = time.time()
                # Cooldown
                if gesture != self.last_triggered_gesture or current_time - self.last_trigger_time > 0.5:
                    self.macro_engine.execute(macro)
                    self.last_trigger_time = current_time
                    self.last_triggered_gesture = gesture
                    macro_triggered = True
                    
            self.current_gesture = gesture
            self.gesture_detected.emit(gesture, confidence)
            
            # Draw status on frame
            h, w, _ = annotated.shape
            
            # Status bar
            cv2.rectangle(annotated, (0, h - 50), (w, h), (30, 30, 30), -1)
            
            # Gesture name
            cv2.putText(annotated, f"Gesture: {gesture.replace('_', ' ').title()}", 
                       (10, h - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Macro trigger indicator
            if macro_triggered:
                cv2.putText(annotated, "MACRO TRIGGERED!", 
                           (w - 200, h - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Convert to Qt image
        rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        # Scale to fit widget
        scaled = qt_image.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, 
                                  Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(QPixmap.fromImage(scaled))


class MacroConfigWidget(QGroupBox):
    """Widget for configuring a gesture's macro."""
    
    def __init__(self, profile_manager):
        super().__init__("Macro Configuration")
        self.profile_manager = profile_manager
        self.current_gesture = None
        
        layout = QFormLayout(self)
        
        # Gesture selector
        self.gesture_combo = QComboBox()
        gestures = self.profile_manager.get_all_gestures()
        for g in gestures:
            self.gesture_combo.addItem(g.replace('_', ' ').title(), g)
        self.gesture_combo.currentIndexChanged.connect(self._on_gesture_changed)
        layout.addRow("Gesture:", self.gesture_combo)
        
        # Current macro display
        self.macro_display = QTextEdit()
        self.macro_display.setMaximumHeight(60)
        self.macro_display.setReadOnly(True)
        layout.addRow("Current Macro:", self.macro_display)
        
        # Key input
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("e.g., ctrl+c or alt+tab or win+d")
        layout.addRow("Keys:", self.key_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._save_macro)
        btn_layout.addWidget(self.save_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear_macro)
        btn_layout.addWidget(self.clear_btn)
        
        layout.addRow(btn_layout)
        
        # Help
        help_label = QLabel("Examples: ctrl+c, alt+tab, win+d, ctrl+shift+esc")
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addRow(help_label)
        
        # Load initial
        self._on_gesture_changed(0)
        
    def _on_gesture_changed(self, index):
        """Load macro for selected gesture."""
        gesture = self.gesture_combo.itemData(index)
        self.current_gesture = gesture
        
        macro = self.profile_manager.get_gesture_macro(gesture)
        if macro and macro.get('action') == 'key_combo':
            keys = macro.get('keys', [])
            self.macro_display.setText('+'.join(keys))
            self.key_input.setText('+'.join(keys))
        else:
            self.macro_display.setText("Not configured")
            self.key_input.clear()
            
    def _save_macro(self):
        """Save the macro configuration."""
        if not self.current_gesture:
            return
            
        keys_text = self.key_input.text().strip()
        if not keys_text:
            QMessageBox.warning(self, "Warning", "Enter at least one key")
            return
            
        keys = [k.strip().lower() for k in keys_text.split('+') if k.strip()]
        macro = {'action': 'key_combo', 'keys': keys}
        
        self.profile_manager.set_gesture_macro(self.current_gesture, macro)
        self.profile_manager.save_profile(
            self.profile_manager._current_profile,
            self.profile_manager.get_current_profile_name()
        )
        
        QMessageBox.information(self, "Saved", 
            f"Saved: {self.current_gesture} → {'+'.join(keys)}")
        self._on_gesture_changed(self.gesture_combo.currentIndex())
        
    def _clear_macro(self):
        """Clear the macro."""
        if not self.current_gesture:
            return
            
        self.profile_manager.set_gesture_macro(self.current_gesture, None)
        self.profile_manager.save_profile(
            self.profile_manager._current_profile,
            self.profile_manager.get_current_profile_name()
        )
        self._on_gesture_changed(self.gesture_combo.currentIndex())


class GestureMacroSimple(QMainWindow):
    """Simple all-in-one GestureMacro window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GestureMacro")
        self.setMinimumSize(1000, 700)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Header
        header = QLabel("🖐️ GestureMacro - Control your computer with hand gestures")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setStyleSheet("padding: 10px; background-color: #2d2d2d; color: white; border-radius: 5px;")
        main_layout.addWidget(header)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Camera panel
        camera_group = QGroupBox("Camera Feed")
        camera_layout = QVBoxLayout(camera_group)
        
        self.camera = CameraWidget()
        camera_layout.addWidget(self.camera)
        
        self.status_label = QLabel("No gesture detected")
        self.status_label.setStyleSheet("font-size: 14px; padding: 5px;")
        camera_layout.addWidget(self.status_label)
        
        splitter.addWidget(camera_group)
        
        # Settings panel
        self.config_widget = MacroConfigWidget(ProfileManager())
        self.config_widget.profile_manager.load_profile("default")
        splitter.addWidget(self.config_widget)
        
        splitter.setSizes([600, 400])
        main_layout.addWidget(splitter)
        
        # Start/Stop button
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶ Start Detection")
        self.start_btn.clicked.connect(self._toggle_detection)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addStretch()
        
        self.status_indicator = QLabel("● Stopped")
        self.status_indicator.setStyleSheet("color: red; font-weight: bold;")
        btn_layout.addWidget(self.status_indicator)
        
        main_layout.addLayout(btn_layout)
        
        # Timer for camera updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.camera.update_frame)
        self.timer.timeout.connect(self._update_status)
        
        self._detection_running = False
        
    def _toggle_detection(self):
        """Start or stop detection."""
        if not self._detection_running:
            if self.camera.start_camera():
                self.timer.start(30)  # ~30 FPS
                self.start_btn.setText("⏹ Stop Detection")
                self.status_indicator.setText("● Running")
                self.status_indicator.setStyleSheet("color: green; font-weight: bold;")
                self._detection_running = True
        else:
            self.timer.stop()
            self.camera.stop_camera()
            self.start_btn.setText("▶ Start Detection")
            self.status_indicator.setText("● Stopped")
            self.status_indicator.setStyleSheet("color: red; font-weight: bold;")
            self._detection_running = False
            
    def _update_status(self):
        """Update status label with current gesture."""
        gesture = self.camera.current_gesture
        if gesture:
            self.status_label.setText(f"Detected: {gesture.replace('_', ' ').title()}")
        else:
            self.status_label.setText("No gesture detected")
            
    def closeEvent(self, event):
        """Clean up on close."""
        self.camera.stop_camera()
        event.accept()


def main():
    # Check for model file
    model_path = os.path.join(os.path.dirname(__file__), 'hand_landmarker.task')
    if not os.path.exists(model_path):
        print(f"Error: Model file not found: {model_path}")
        print("Download from: https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    
    # Set dark style
    app.setStyle('Fusion')
    
    window = GestureMacroSimple()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
