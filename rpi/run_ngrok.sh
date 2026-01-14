#!/bin/bash

# 1. הפעלת Ngrok ברקע (שים לב לסימן & בסוף)
echo "Starting Ngrok..."
ngrok http --domain=solenoidally-nonbearded-rocco.ngrok-free.dev 8765 > /dev/null &

# 2. המתנה קצרה כדי לוודא ש-Ngrok התחבר
echo "Waiting for Ngrok to connect..."
sleep 5

# 3. הפעלת המערכת הראשית (פייתון)
echo "Starting Main System..."
# שימוש בנתיב המלא לפייתון ולסקריפט כדי למנוע טעויות
/home/afik191/EyesOn/venv/bin/python /home/afik191/EyesOn/rpi/main_system.py
