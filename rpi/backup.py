import sys
import os
import cv2
import asyncio
import websockets
import base64
import time
import threading
import queue
import subprocess
from ultralytics import YOLO

# --- RPi 5 Fix: Load Camera Driver ---
sys.path.append('/usr/lib/python3/dist-packages')

try:
    from picamera2 import Picamera2
    print("Success: Picamera2 loaded!")
except ImportError:
    print("Error: Could not load Picamera2. Run 'sudo apt install python3-picamera2'")
    sys.exit(1)

# ---------------- CONFIGURATION ----------------
PORT = 8765
HEADLESS_MODE = True

KNOWN_OBJECTS = [
    'car', 'bus', 'truck', 'bicycle', 'motorcycle', 'person',
    'dog', 'cat', 'fire hydrant', 'bench', 'stop sign',
    'traffic light', 'chair'
]

AREA_THRESHOLD = 0.60
CONF_THRESHOLD = 0.45
PER_ID_COOLDOWN_SEC = 4.0
GLOBAL_COOLDOWN_SEC = 1.5
USE_CENTER_CORRIDOR = True
CENTER_CORRIDOR_WIDTH_RATIO = 0.55

PRIORITY = {
    "person": 5, "bicycle": 4, "motorcycle": 4,
    "car": 3, "bus": 3, "truck": 3,
    "dog": 2, "cat": 2, "traffic light": 1,
    "stop sign": 1, "fire hydrant": 1, "bench": 1, "chair": 1,
}

# ---------------- LOGGING SYSTEM ----------------
log_queue = queue.Queue()

def broadcast_log(message):
    """Prints to terminal and queues for web interface"""
    print(f"ℹ️ {message}")
    log_queue.put(f"LOG:{message}")

# ---------------- AUDIO SYSTEM (TTS) ----------------
speech_queue = queue.Queue()

def speaker_worker():
    broadcast_log("🔊 Speaker thread active (Using System Default)")
    
    # Get the current user ID
    user_id = os.getuid()

    while True:
        try:
            text_to_speak = speech_queue.get(timeout=1)
            if text_to_speak is None: break
            
            broadcast_log(f"🗣️ Speaking: {text_to_speak}")
            
            # Inject audio environment variables for espeak
            cmd = (
                f'export XDG_RUNTIME_DIR=/run/user/{user_id}; '
                f'export PULSE_SERVER=unix:/run/user/{user_id}/pulse/native; '
                f'espeak -a 200 -s 150 "{text_to_speak}" --stdout | pw-play - 2>/dev/null'
            )
            
            os.system(cmd)

            speech_queue.task_done()
        except queue.Empty:
            continue

threading.Thread(target=speaker_worker, daemon=True).start()

# ---------------- STATE ----------------
last_spoken_by_id = {}
last_global_spoken = 0.0
connected_clients = set()

def can_speak(track_id: int) -> bool:
    t = time.time()
    if t - last_global_spoken < GLOBAL_COOLDOWN_SEC: return False
    last_t = last_spoken_by_id.get(track_id, 0.0)
    if t - last_t < PER_ID_COOLDOWN_SEC: return False
    return True

def mark_spoken(track_id: int):
    global last_global_spoken
    t = time.time()
    last_spoken_by_id[track_id] = t
    last_global_spoken = t

# ---------------- WEBSOCKET HANDLER (AUDIO IN + OUT) ----------------
async def handler(websocket):
    broadcast_log(f"Client connected: {websocket.remote_address}")
    connected_clients.add(websocket)
    
    # --- AUDIO FIX FOR WALKIE-TALKIE ---
    # Prepare environment variables for the subprocess (ffplay)
    # This ensures ffplay knows where the Bluetooth speakers are even when running as a service
    user_id = os.getuid()
    audio_env = os.environ.copy()
    audio_env["XDG_RUNTIME_DIR"] = f"/run/user/{user_id}"
    audio_env["PULSE_SERVER"] = f"unix:/run/user/{user_id}/pulse/native"

    # Walkie-Talkie Player
    audio_process = None
    
    try:
        async for message in websocket:
            if isinstance(message, bytes):
                # If binary audio data arrives, open player (FFplay)
                if audio_process is None or audio_process.poll() is not None:
                    audio_process = subprocess.Popen(
                        ['ffplay', '-nodisp', '-autoexit', '-probesize', '32', '-sync', 'audio', '-i', 'pipe:0'],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        env=audio_env  # <--- CRITICAL FIX: Injecting audio config
                    )
                try:
                    audio_process.stdin.write(message)
                    audio_process.stdin.flush()
                except Exception as e:
                    print(f"Audio write error: {e}")

    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        connected_clients.remove(websocket)
        if audio_process:
            audio_process.kill()
        broadcast_log("Client disconnected")

# ---------------- MAIN LOOP (VIDEO OUT) ----------------
async def run_system():
    broadcast_log("⏳ Loading YOLOv11 model...")
    model = YOLO("yolo11n.pt")

    broadcast_log("📷 Starting Camera...")
    picam2 = Picamera2()
    config = picam2.create_video_configuration(main={"size": (640, 480), "format": "BGR888"})
    picam2.configure(config)
    picam2.start()

    speech_queue.put("System Online")
    broadcast_log("✅ System Ready")

    SCREEN_W, SCREEN_H = 640, 480
    FRAME_AREA = SCREEN_W * SCREEN_H
    CENTER_X = SCREEN_W / 2
    corridor_half = (SCREEN_W * CENTER_CORRIDOR_WIDTH_RATIO) / 2
    corridor_left, corridor_right = CENTER_X - corridor_half, CENTER_X + corridor_half

    try:
        while True:
            frame = picam2.capture_array()
            results = model.track(frame, persist=True, verbose=False, tracker="bytetrack.yaml")
            display_frame = frame.copy() 

            best = None
            for result in results:
                if result.boxes is None: continue
                for box in result.boxes:
                    if box.id is None: continue

                    track_id = int(box.id[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    w, h = max(0, x2 - x1), max(0, y2 - y1)
                    class_id = int(box.cls[0])
                    name = model.names[class_id]
                    conf = float(box.conf[0])

                    if name not in KNOWN_OBJECTS or conf < CONF_THRESHOLD: continue
                    area_ratio = (w * h) / FRAME_AREA
                    if area_ratio < AREA_THRESHOLD: continue

                    obj_center_x = x1 + w / 2
                    if USE_CENTER_CORRIDOR and (obj_center_x < corridor_left or obj_center_x > corridor_right):
                        continue

                    direction = "Move Right" if obj_center_x < CENTER_X else "Move Left"
                    msg = f"{direction}, {name} ahead"
                    pr = PRIORITY.get(name, 1)
                    score = (area_ratio * 100.0) + (pr * 10.0) + conf

                    if best is None or score > best["score"]:
                        best = {"score": score, "track_id": track_id, "name": name, "msg": msg, "coords": (x1, y1, x2, y2)}

            if best:
                if can_speak(best["track_id"]):
                    broadcast_log(f"🚨 ALERT: {best['msg']}")
                    speech_queue.put(best["msg"])
                    mark_spoken(best["track_id"])
                
                x1, y1, x2, y2 = best["coords"]
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                cv2.putText(display_frame, f"ALERT: {best['name']}", (x1, max(20, y1-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            if USE_CENTER_CORRIDOR:
                cv2.line(display_frame, (int(corridor_left), 0), (int(corridor_left), SCREEN_H), (255, 255, 255), 1)
                cv2.line(display_frame, (int(corridor_right), 0), (int(corridor_right), SCREEN_H), (255, 255, 255), 1)

            # Broadcast Image AND Logs
            if connected_clients:
                logs_to_send = []
                while not log_queue.empty():
                    try: logs_to_send.append(log_queue.get_nowait())
                    except queue.Empty: break
                
                small_frame = cv2.resize(display_frame, (320, 240))
                _, buffer = cv2.imencode('.jpg', small_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                jpg_as_text = base64.b64encode(buffer).decode('utf-8')

                tasks = []
                disconnected = set()
                for client in connected_clients:
                    try:
                        # First send the image
                        tasks.append(client.send(jpg_as_text))
                        # Then send all accumulated logs
                        for log_msg in logs_to_send: tasks.append(client.send(log_msg))
                    except websockets.exceptions.ConnectionClosed:
                        disconnected.add(client)
                
                if tasks: await asyncio.gather(*tasks, return_exceptions=True)
                connected_clients.difference_update(disconnected)

            await asyncio.sleep(0.001)

    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        picam2.stop()
        cv2.destroyAllWindows()

async def main():
    async with websockets.serve(handler, "0.0.0.0", PORT):
        broadcast_log(f"📡 WebSocket Server running on port {PORT}")
        await run_system()

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: pass