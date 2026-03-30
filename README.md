# 🖐️ GestureDeck

**Control your computer with hand gestures** - A programmable macro launcher powered by computer vision.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Hand_Tracking-orange.svg)

---

## ✨ Features

- **15 Hand Gestures** - Finger counts (0-10) + special signs (peace, OK, thumbs up, point, fist)
- **Programmable Macros** - Map each gesture to keyboard shortcuts
- **Profile System** - Save/load configurations for different use cases
- **Real-time Detection** - Low-latency hand tracking with MediaPipe
- **Visual Feedback** - See detected gestures and macro triggers live
- **Easy Configuration** - Built-in GUI for mapping gestures to actions

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/gesture-deck.git
cd gesture-deck
pip install -r requirements.txt
```

### 2. Download Model File

Download the MediaPipe hand landmarker model (~7.5 MB):

```bash
# Option 1: Using curl
curl -L -o hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task

# Option 2: Using PowerShell
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" -OutFile "hand_landmarker.task"
```

Or download manually from: [MediaPipe Model](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task)

### 3. Run

```bash
python gesture_deck.py
```

---

## 📖 Usage

1. **Click "Start Detection"** to enable the camera
2. **Select a gesture** from the dropdown (e.g., "Fist", "Peace", "Two")
3. **Enter keyboard shortcuts** (e.g., `ctrl+c`, `alt+tab`, `win+d`)
4. **Click Save** to store the mapping
5. **Make the gesture** in front of your camera to trigger the macro!

---

## 👋 Supported Gestures

| Gesture | Description | Default Action |
|---------|-------------|----------------|
| ✊ Fist | All fingers curled | Win+D (Show Desktop) |
| ☝️ One | Index finger up | Ctrl+C (Copy) |
| ✌️ Two | Index + middle up | Ctrl+V (Paste) |
| 🤟 Three | Three fingers up | Alt+Tab (Switch Window) |
| 🖐️ Four | Four fingers up | Ctrl+Shift+Esc (Task Manager) |
| 🖐️ Five | Open hand | Win+E (File Explorer) |
| 🤟 Six | Five + one | Ctrl+T (New Tab) |
| 🤟 Seven | Five + two | Ctrl+W (Close Tab) |
| 🤟 Eight | Five + three | Ctrl+Shift+T (Reopen Tab) |
| 🤟 Nine | Five + four | Ctrl+Tab (Next Tab) |
| 🙌 Ten | Both hands open | Win+L (Lock Screen) |
| ✌️ Peace | V sign | Ctrl+Alt+M (Custom) |
| 👌 OK | Thumb+index circle | Ctrl+Alt+P (Custom) |
| 👍 Thumbs Up | Thumb extended | Ctrl+Alt+Up (Custom) |
| 👆 Point | Index pointing | Ctrl+Alt+Down (Custom) |

---

## 🛠️ Configuration

### Macro Format

Macros are stored in `profiles/default.json`:

```json
{
  "action": "key_combo",
  "keys": ["ctrl", "shift", "esc"]
}
```

### Supported Actions

| Action | Parameters | Example |
|--------|------------|---------|
| `key_combo` | `keys: string[]` | `["ctrl", "c"]` |
| `text` | `text: string` | `"Hello, World!"` |

### Key Names

- **Modifiers**: `ctrl`, `alt`, `shift`, `win`
- **Letters**: `a` through `z`
- **Numbers**: `0` through `9`
- **Special**: `enter`, `tab`, `space`, `backspace`, `escape`, `up`, `down`, `left`, `right`
- **Function keys**: `f1` through `f12`

---

## 📁 Project Structure

```
gesture-deck/
├── gesture_deck.py          # Main application (run this!)
├── gesture_detector.py      # Hand tracking & gesture classification
├── macro_engine.py          # Keyboard simulation engine
├── profile_manager.py       # Profile save/load management
├── gui/
│   ├── __init__.py
│   └── settings_window.py   # PyQt6 settings UI components
├── profiles/
│   └── default.json         # Default gesture mappings
├── hand_landmarker.task     # MediaPipe ML model (download separately)
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── LICENSE                 # MIT License
└── .gitignore
```

---

## 💡 Tips

- **Lighting**: Good, even lighting improves detection accuracy
- **Distance**: Position your hand 1-2 feet from the camera
- **Visibility**: Keep your full hand visible in the frame
- **Cooldown**: 0.5s delay between same-gesture triggers prevents accidents
- **Custom shortcuts**: Use `ctrl+alt+[key]` for custom bindings that won't conflict

---

## 🧰 Tech Stack

| Component | Technology |
|-----------|------------|
| Computer Vision | MediaPipe Hands |
| Image Processing | OpenCV |
| GUI Framework | PyQt6 |
| Input Simulation | pynput |
| Numerical Ops | NumPy |

---

## 🔧 Development

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Tests

```bash
# Test gesture detector
python gesture_detector.py

# Test profile manager
python profile_manager.py

# Test macro engine
python macro_engine.py
```

---

## ⚠️ Troubleshooting

**Camera not detected:**
- Ensure no other application is using the camera
- Check Windows privacy settings for camera access

**Gestures not recognized:**
- Improve lighting (face your light source)
- Move hand closer/further to find optimal range
- Ensure full hand is visible in frame

**Macros not executing:**
- Some applications require admin privileges for keyboard input
- Try running as Administrator for certain apps

**Media keys not working:**
- Media keys may require additional drivers or admin rights
- Use alternative keyboard shortcuts instead

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Additional gesture recognition (ASL alphabet)
- [ ] Mouse control macros
- [ ] Application-specific profiles (auto-switch based on active window)
- [ ] Gesture sequence macros (combo moves)
- [ ] Multi-hand independent mappings

---

## 🙏 Acknowledgments

- [MediaPipe](https://mediapipe.dev) for hand tracking
- [OpenCV](https://opencv.org) for computer vision
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for the GUI

---

<p align="center">Made with ❤️ using Python & Computer Vision</p>
