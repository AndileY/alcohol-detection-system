## 📋 Complete README Content

Click the copy button in the top-right corner of the code block below to copy everything:


# Alcohol Detection System

Complete alcohol detection system with Arduino KS0397, face recognition, and real-time web dashboard with MQTT integration.



## 📋 Project Overview

- **Hardware:** Keyestudio KS0397 with MQ-3 sensor
- **Face Detection:** OpenCV Haar Cascade
- **Backend:** Flask + Socket.IO
- **Dashboard:** Real-time HTML/CSS/JS
- **MQTT:** test.mosquitto.org
- **Communication:** Serial (USB) + MQTT



## 🧪 Hardware Requirements

- Keyestudio KS0397 Arduino board
- MQ-3 Alcohol Sensor
- 2x LEDs (Red/Blue/Green)
- 1x Push Button
- USB Cable



## 🔧 Software Requirements

- Arduino IDE
- Python 3.x
- Flask
- OpenCV
- paho-mqtt
- Socket.IO



## 🚀 Getting Started

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/alcohol-detection-system.git
cd alcohol-detection-system
```

### Step 2: Upload Arduino Code

Open `arduino/alcohol_system.ino` in Arduino IDE
Select Tools → Board → Arduino/Genuino Uno
Select Tools → Port (e.g., COM10)
Click Upload

### Step 3: Install Python Dependencies

```bash
cd python
pip install -r requirements.txt
```

**requirements.txt:**
```text
opencv-python
pyserial
paho-mqtt
flask
flask-socketio
flask-cors
eventlet
```

### Step 4: Run the MQTT Bridge (Python)

```bash
python arduino_mqtt_bridge.py
```

This script:
- Reads serial data from Arduino
- Runs face recognition using OpenCV
- Publishes data to MQTT broker

### Step 5: Run the Web Dashboard

```bash
cd web
python app.py
```

The dashboard will be available at:
- Dashboard: http://localhost:5000
- Analytics: http://localhost:5000/analytics
- History: http://localhost:5000/history
- Settings: http://localhost:5000/settings

### Step 6: Test the System

1. Press the button on the KS0397 board
2. Look at the camera for face verification
3. Blow into the MQ-3 sensor
4. Check the web dashboard for real-time results

---

## 📁 Project Structure

```
alcohol-detection-system/
│
├── arduino/
│   └── alcohol_system.ino          # KS0397 Arduino code (inverted logic)
│
├── python/
│   ├── arduino_mqtt_bridge.py      # Face recognition + MQTT bridge
│   └── requirements.txt            # Python dependencies
│
├── web/
│   ├── app.py                      # Flask web server
│   ├── templates/
│   │   ├── index.html              # Dashboard
│   │   ├── analytics.html          # Analytics page
│   │   ├── history.html            # History page
│   │   └── settings.html           # Settings page
│   └── static/                     # CSS/JS files (if any)
│
└── README.md                       # This file
```

---

## 🏗️ Architecture

### System Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ALCOHOL DETECTION SYSTEM                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐             │
│  │  User Press │    │  Face Scan  │    │  Blow into MQ-3     │             │
│  │   Button    │───▶│  (OpenCV)   │───▶│    Sensor           │             │
│  └─────────────┘    └─────────────┘    └─────────────────────┘             │
│                          │                      │                          │
│                          ▼                      ▼                          │
│                  ┌─────────────┐    ┌────────────────────────┐             │
│                  │  Face       │    │  Inverted Logic        │             │
│                  │  Verified?  │    │  Clean Air = 1000+     │             │
│                  └──────┬──────┘    │  Alcohol = 50-100      │             │
│                         │           └────────────┬───────────┘             │
│                         ▼                        │                         │
│                  ┌─────────────┐                 │                         │
│                  │  Send 'V'   │                 │                         │
│                  │  to Arduino │                 │                         │
│                  └──────┬──────┘                 │                         │
│                         │                        │                         │
│                         └──────────┬─────────────┘                         │
│                                    ▼                                       │
│                    ┌───────────────────────────────────┐                   │
│                    │       RESULT                      │                   │
│                    ├───────────────────────────────────┤                   │
│                    │  ✅ GRANTED (Blue LED)            │                   │
│                    │  ❌ DENIED (Red LED)              │                   │
│                    └─────────────────┬─────────────────┘                   │
│                                      ▼                                     │
│                    ┌───────────────────────────────────┐                   │
│                    │       MQTT PUBLISH                │                   │
│                    │  test.mosquitto.org:1883          │                   │
│                    ├───────────────────────────────────┤                   │
│                    │  /alcohol_system/status           │                   │
│                    │  /alcohol_system/face             │                   │
│                    │  /alcohol_system/sensor           │                   │
│                    │  /alcohol_system/alcohol_result   │                   │
│                    │  /alcohol_system/percentage       │                   │
│                    └─────────────────┬─────────────────┘                   │
│                                      ▼                                     │
│                    ┌───────────────────────────────────┐                   │
│                    │       WEB DASHBOARD               │                   │
│                    │  Flask + Socket.IO                │                   │
│                    ├───────────────────────────────────┤                   │
│                    │  📊 Live Dashboard                │                   │
│                    │  📈 Analytics                     │                   │
│                    │  📜 History                       │                   │
│                    │  ⚙️ Settings                      │                   │
│                    └───────────────────────────────────┘                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📸 Screenshots

### Dashboard
*Real-time alcohol detection monitoring*

<img width="1200" height="600" alt="Dashboard" src="https://via.placeholder.com/1200x600?text=Dashboard+Screenshot" />

### Analytics
*Statistical analysis and trends*

<img width="1200" height="600" alt="Analytics" src="https://via.placeholder.com/1200x600?text=Analytics+Screenshot" />

### History
*Past detection records and logs*

<img width="1200" height="600" alt="History" src="https://via.placeholder.com/1200x600?text=History+Screenshot" />

### Settings
*Configuration and system settings*

<img width="1200" height="600" alt="Settings" src="https://via.placeholder.com/1200x600?text=Settings+Screenshot" />

---

## 📦 Technologies Used

| Technology | Purpose |
|------------|---------|
| Arduino C++ | Hardware control |
| Python | Face recognition + MQTT bridge |
| Flask | Web server |
| Socket.IO | Real-time updates |
| MQTT | Data streaming |
| OpenCV | Face detection |

---

## 📝 Features Checklist

| Feature | Status |
|---------|--------|
| Arduino KS0397 Integration | ✅ |
| MQ-3 Alcohol Sensor | ✅ |
| Face Recognition (OpenCV) | ✅ |
| MQTT Communication | ✅ |
| Real-time Dashboard | ✅ |
| Analytics Page | ✅ |
| History Logging | ✅ |
| Settings Configuration | ✅ |
| Serial Communication | ✅ |
| LED Indicators | ✅ |
| Push Button Trigger | ✅ |

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Arduino not detected | Check USB connection and port |
| Serial permission denied | Run with sudo or add user to dialout group |
| MQTT connection failed | Check internet connection and broker status |
| Camera not working | Verify OpenCV installation and camera permissions |
| Flask port in use | Change port number in app.py |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project was created for **enterprise alcohol detection** purposes.

---

**Made with ❤️ for enterprise alcohol detection**
```
