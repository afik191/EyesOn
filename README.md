# EyesOn 
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
* Raspberry Pi Camera Module 3 (Picamera2)
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



