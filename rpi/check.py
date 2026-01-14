import time
import os
import cv2
import threading
import queue
from ultralytics import YOLO
from picamera2 import Picamera2

# ---------------- CONFIG ----------------
HEADLESS_MODE = False

# Your exact list (unchanged)
KNOWN_OBJECTS = [
    'car', 'bus', 'truck', 'bicycle', 'motorcycle', 'person',
    'dog', 'cat', 'fire hydrant', 'bench', 'stop sign',
    'traffic light', 'chair'
]

# Speak only if the object occupies >= 60% of the frame area
AREA_THRESHOLD = 0.60  # 60% of total frame area

# Detection confidence threshold
CONF_THRESHOLD = 0.45

# Speak rate limits
PER_ID_COOLDOWN_SEC = 4.0     # same tracked object won't be repeated too often
GLOBAL_COOLDOWN_SEC = 1.5     # don't speak too frequently overall

# Optional: only alert for objects in the central corridor (reduces "background" alerts)
USE_CENTER_CORRIDOR = True
CENTER_CORRIDOR_WIDTH_RATIO = 0.55  # 55% of screen width around center

# Optional priorities (helps choose TOP-1 if multiple are huge)
PRIORITY = {
    "person": 5,
    "bicycle": 4,
    "motorcycle": 4,
    "car": 3,
    "bus": 3,
    "truck": 3,
    "dog": 2,
    "cat": 2,
    "traffic light": 1,
    "stop sign": 1,
    "fire hydrant": 1,
    "bench": 1,
    "chair": 1,
}

# ---------------- AUDIO SYSTEM ----------------
speech_queue = queue.Queue()

def speaker_worker():
    print("🔊 Speaker thread active...")
    while True:
        try:
            text_to_speak = speech_queue.get(timeout=1)
            if text_to_speak is None:
                break
            print(f"🗣️ Executing Speech: {text_to_speak}")
            os.system(f'espeak -a 200 -s 150 "{text_to_speak}"')
            speech_queue.task_done()
        except queue.Empty:
            continue

threading.Thread(target=speaker_worker, daemon=True).start()

# ---------------- YOLO MODEL ----------------
print("⏳ Loading YOLO...")
model = YOLO("yolo11n.pt")

# ---------------- COOLDOWN STATE ----------------
last_spoken_by_id = {}  # track_id -> last spoken time
last_global_spoken = 0.0

def now():
    return time.time()

def can_speak(track_id: int) -> bool:
    t = now()
    if t - last_global_spoken < GLOBAL_COOLDOWN_SEC:
        return False
    last_t = last_spoken_by_id.get(track_id, 0.0)
    if t - last_t < PER_ID_COOLDOWN_SEC:
        return False
    return True

def mark_spoken(track_id: int):
    global last_global_spoken
    t = now()
    last_spoken_by_id[track_id] = t
    last_global_spoken = t

# ---------------- CAMERA SETUP ----------------
print("📷 Initializing Camera...")
picam2 = None

try:
    picam2 = Picamera2()
    config = picam2.create_video_configuration(
        main={"size": (640, 480), "format": "BGR888"}
    )
    picam2.configure(config)
    picam2.start()

    speech_queue.put("System Startup Successful")
    print("✅ System Ready. Watching for objects...")

    SCREEN_W, SCREEN_H = 640, 480
    FRAME_AREA = SCREEN_W * SCREEN_H
    CENTER_X = SCREEN_W / 2

    corridor_half = (SCREEN_W * CENTER_CORRIDOR_WIDTH_RATIO) / 2
    corridor_left = CENTER_X - corridor_half
    corridor_right = CENTER_X + corridor_half

    while True:
        frame = picam2.capture_array()

        # Track objects
        results = model.track(
            frame,
            persist=True,
            verbose=False,
            tracker="bytetrack.yaml"
        )

        display_frame = frame.copy() if not HEADLESS_MODE else None

        # Collect candidates and pick the single best (TOP-1)
        best = None
        # best = dict(score, track_id, name, msg, coords, area_ratio, conf)

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                if box.id is None:
                    continue

                track_id = int(box.id[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                w = max(0, x2 - x1)
                h = max(0, y2 - y1)

                class_id = int(box.cls[0])
                name = model.names[class_id]
                conf = float(box.conf[0])

                # Filter by class + confidence
                if name not in KNOWN_OBJECTS:
                    continue
                if conf < CONF_THRESHOLD:
                    continue

                area = w * h
                area_ratio = area / FRAME_AREA

                # MAIN RULE: Only alert if >= 60% of frame area
                if area_ratio < AREA_THRESHOLD:
                    continue

                obj_center_x = x1 + w / 2

                # Optional corridor filter
                if USE_CENTER_CORRIDOR:
                    if obj_center_x < corridor_left or obj_center_x > corridor_right:
                        continue

                direction = "Move Right" if obj_center_x < CENTER_X else "Move Left"
                msg = f"{direction}, {name} ahead"

                # Score: primarily size, then priority, then confidence
                pr = PRIORITY.get(name, 1)
                score = (area_ratio * 100.0) + (pr * 10.0) + conf

                if best is None or score > best["score"]:
                    best = {
                        "score": score,
                        "track_id": track_id,
                        "name": name,
                        "msg": msg,
                        "coords": (x1, y1, x2, y2),
                        "area_ratio": area_ratio,
                        "conf": conf,
                    }

        # Speak only the best candidate
        if best is not None:
            tid = best["track_id"]
            if can_speak(tid):
                print(f"🚨 ALERT: {best['msg']} (area={best['area_ratio']:.2f}, conf={best['conf']:.2f})")
                speech_queue.put(best["msg"])
                mark_spoken(tid)

            if not HEADLESS_MODE:
                x1, y1, x2, y2 = best["coords"]
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                cv2.putText(
                    display_frame,
                    f"ALERT: {best['name']} area={best['area_ratio']:.2f}",
                    (x1, max(20, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )

        if not HEADLESS_MODE:
            # Draw corridor for debug
            if USE_CENTER_CORRIDOR:
                cv2.line(display_frame, (int(corridor_left), 0), (int(corridor_left), SCREEN_H), (255, 255, 255), 1)
                cv2.line(display_frame, (int(corridor_right), 0), (int(corridor_right), SCREEN_H), (255, 255, 255), 1)

            cv2.imshow("Smart Hat Debug", display_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

except Exception as e:
    print(f"❌ Error: {e}")

finally:
    print("Cleaning up...")
    speech_queue.put("Shutting down")
    time.sleep(1.5)
    try:
        if picam2 is not None:
            picam2.stop()
    except:
        pass
    cv2.destroyAllWindows()
    speech_queue.put(None)