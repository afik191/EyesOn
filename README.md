
### AI-Powered Assistive Wearable for the Visually Impaired

**EyesOn** is a smart wearable system designed to assist visually impaired individuals navigate their surroundings safely. Powered by a **Raspberry Pi 5** and **YOLOv11**, the system detects obstacles in real-time, provides directional audio feedback, and allows a remote caregiver to view a live feed and communicate via a **Walkie-Talkie** feature.

![Project Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![React](https://img.shields.io/badge/React-Vite-61DAFB)
![YOLO](https://img.shields.io/badge/AI-YOLOv11-orange)
![Hardware](https://img.shields.io/badge/Hardware-Raspberry_Pi_5-C51A4A)

---

##  Features

* **Real-Time Object Detection:** Uses YOLOv11n to identify objects (Person, Car, Bench, etc.).
* **Directional Audio Feedback:** TTS (Text-to-Speech) alerts the user on where to move ("Move Right, person ahead").
* **Live Dashboard:** A React-based web interface showing the live video stream and system logs.
* **Two-Way Audio (Walkie-Talkie):** Remote caregivers can speak through the website, and audio is played instantly on the user's Bluetooth headset.
* **Automatic Connectivity:** Self-healing connection using Ngrok and Systemd services.
* **Smart Audio Routing:** Automatically detects and connects to Bluetooth devices (AirPods/JBL).

---

##  Tech Stack

### Hardware
* Raspberry Pi 5
* Raspberry Pi Camera Module v2.1 (Picamera2)
* Bluetooth Headset (AirPods / JBL)
* Power Bank (for portability)

### Software
* **Backend (RPi):** Python, OpenCV, Ultralytics YOLO, WebSockets, PipeWire/PulseAudio, FFmpeg.
* **Frontend (Client):** React.js, Vite, WebSocket API.
* **Infrastructure:** Ngrok (Tunneling), Systemd (Service Management).

---

##  Project Structure

```bash
EyesOn/
├── rpi/                 # Raspberry Pi Code (Backend)
│   ├── main_system.py   # Core logic (YOLO, Camera, Audio, WebSocket)
│   ├── run_ngrok.sh     # Startup script (Ngrok + Audio Config)
│   ├── yolo11n.pt       # AI Model weights
│   └── ...
├── camera-client/       # Web Dashboard (Frontend)
│   ├── src/
│   │   ├── VideoStream.jsx # Main Interface Component
│   │   └── ...
│   └── package.json
└── README.md
```
## Installation & Setup
1. Raspberry Pi (Backend)
Prerequisites:

* Raspberry Pi 5 with Raspberry Pi OS (Bookworm).

* Python 3.11+

* ```ffmpeg``` and ```espeak``` installed.

setup:
```bash
# Clone the repository
git clone https://github.com/afik191/EyesOn.git
cd EyesOn/rpi

# Install dependencies
pip install ultralytics opencv-python websockets picamera2

# Install system audio tools
sudo apt update && sudo apt install ffmpeg espeak pulseaudio-utils -y
```
Auto-Start Service: The system runs automatically on boot using a Systemd service.
```bash
sudo cp smart-hat.service /etc/systemd/system/
sudo systemctl enable smart-hat.service
sudo systemctl start smart-hat.service
```

2. Web Client (Frontend)
Setup:
```bash
cd camera-client
npm install
```
Run Locally:
```bash
npm run dev
```
Note: The frontend is deployed on Vercel for production.


## Usage
1. Power On: Connect the power bank to the Raspberry Pi.

2. Auto-Connect: The system automatically connects to the configured WiFi and Bluetooth headset.

3. Monitoring: The caregiver accesses the Vercel link.

4. Interaction:

    * View: Live video stream and detection logs appear on screen.

    * Talk: Hold the "HOLD TO TALK" button to speak to the user.


## Screenshots
<img width="700" height="800" alt="{D5EC4E3C-26DA-4E13-8460-EFE84305BC9B}" src="https://github.com/user-attachments/assets/84c59f57-e23d-48d7-b3db-1f6aad877250" />

---

##  Field Testing & Observations

During the testing phase, we identified a slight latency between real-world events and the audio alerts. Additionally, a **"Low Voltage"** warning appeared on the Raspberry Pi when powered by a portable battery.

We conducted a deep investigation with faculty assistance, including physical voltage measurements:
* **Wall Charger:** Measured **5.01V**.
* **Power Bank:** Measured **4.97V**.

**Conclusion:**
Despite the negligible voltage difference, the system still triggered low-voltage warnings. Our hypothesis is that the portable battery struggles to supply stable **current** (Amps) during peak processing moments (throttling), causing performance dips that couldn't be isolated by voltage measurements alone.

###  Limitations
* **Lighting Conditions:** The current camera module performs poorly in low-light environments, limiting the system's effectiveness primarily to daytime use.

---

##  Future Work & Recommendations

Based on our findings, we recommend the following upgrades for the next version:

1.  **Hardware Upgrade:** Switch to a camera with a **Low Light / Night Vision** sensor or a **Global Shutter** camera to improve detection reliability in motion and darkness.
2.  **Power Supply:** Upgrade to a battery bank that supports **PD (Power Delivery)** protocol with 5A output. This should resolve the "Low Voltage" throttling and improve system response time.



