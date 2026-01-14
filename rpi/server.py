import sys
import os
import cv2
import asyncio
import websockets
import base64
import time
from ultralytics import YOLO


# --- RPi 5 Fix: Load Picamera2 from system packages ---
# This allows the venv to access the camera driver located in the system folder
sys.path.append('/usr/lib/python3/dist-packages')


try:
    from picamera2 import Picamera2
    print("Success: Picamera2 loaded!")
except ImportError:
    print("Error: Could not load Picamera2. Run 'sudo apt install python3-picamera2'")
    sys.exit(1)
# -----------------------------------------------

PORT = 8765

print("Loading YOLOv11 model...")
model = YOLO('yolo11n.pt') 

print("Starting Camera (Picamera2)...")
picam2 = Picamera2()

# Important change: Set BGR888 to match OpenCV and YOLO directly
# This saves manual color conversion and reduces CPU usage
config = picam2.create_video_configuration(main={"size": (640, 480), "format": "BGR888"})
picam2.configure(config)
picam2.start()

connected_clients = set()

async def handler(websocket):
    print(f"Client connected: {websocket.remote_address}")
    connected_clients.add(websocket)
    try:
        await websocket.wait_closed()
    except:
        pass
    finally:
        connected_clients.remove(websocket)
        print("Client disconnected")

async def broadcast_frames():
    print("Starting broadcast loop...")
    try:
        while True:
            # 1. Capture image (already in BGR format)
            frame = picam2.capture_array()

            # 2. Object detection
            # imgsz=320 significantly speeds up detection
            results = model(frame, verbose=False, imgsz=320, conf=0.5)
            
            # 3. Draw bounding boxes on the image
            # results[0].plot() returns the image in BGR format
            annotated_frame = results[0].plot()

            if annotated_frame is None:
                annotated_frame = frame

            # 4. Resize for fast WiFi streaming
            small_frame = cv2.resize(annotated_frame, (320, 240))
            
            # Note: Removed cvtColor because camera is pre-configured for BGR
            
            # 5. Encode to JPG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
            _, buffer = cv2.imencode('.jpg', small_frame, encode_param)
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')

            # 6. Broadcast to all connected clients
            if connected_clients:
                tasks = []
                disconnected_clients = set()
                
                for client in connected_clients:
                    try:
                        tasks.append(client.send(jpg_as_text))
                    except websockets.exceptions.ConnectionClosed:
                        disconnected_clients.add(client)
                
                if tasks:
                    # Send to all clients in parallel
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                # Clean up disconnected clients
                connected_clients.difference_update(disconnected_clients)
            
            # Small CPU rest
            await asyncio.sleep(0.001)

    except Exception as e:
        print(f"Error in broadcast: {e}")
    finally:
        picam2.stop()
        print("Camera stopped")

async def main():
    # Start the WebSocket server
    async with websockets.serve(handler, "0.0.0.0", PORT):
        print(f"WebSocket Server started on port {PORT}")
        # Run the broadcast loop
        await broadcast_frames()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        # Ensure camera shutdown in case of crash
        try:
            picam2.stop()
        except:
            pass