import cv2
import time
from datetime import datetime
import os

mouse_name = input("Enter mouse name: ").strip()

if mouse_name == "":
    raise ValueError("Mouse name cannot be empty")

save_folder = os.path.join("recordings", mouse_name)
os.makedirs(save_folder, exist_ok=True)

session_time = datetime.now().strftime("%Y%m%d_%H%M%S")

video_path = os.path.join(save_folder, f"{mouse_name}_{session_time}.avi")
timestamp_path = os.path.join(save_folder, f"{mouse_name}_{session_time}_timestamps.txt")

cap = cv2.VideoCapture(0, cv2.CAP_MSMF)

cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))


cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

cap.set(cv2.CAP_PROP_FPS, 30)

ret, frame = cap.read()
if not ret:
    raise RuntimeError("Could not read from webcam")

height, width = frame.shape[:2]

print("Actual camera frame size:", width, height)
print("Camera-reported FPS:", cap.get(cv2.CAP_PROP_FPS))
print("Saving video to:", video_path)
print("Saving timestamps to:", timestamp_path)

# Center-crop to square
square_size = min(width, height)

save_fps = 30

out = cv2.VideoWriter(
    video_path,
    cv2.VideoWriter_fourcc(*"MJPG"),
    save_fps,
    (square_size, square_size)
)

if not out.isOpened():
    cap.release()
    raise RuntimeError("Could not open VideoWriter")

log_file = open(timestamp_path, "w", encoding="utf-8")
log_file.write("frame\ttime\n")

print("\nPreview started.")
print("Press Esc to START recording.")
print("After recording starts, press q or Esc to STOP.\n")

# -------------------------
# Preview first
# -------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        print("Frame read failed during preview")
        break

    h, w = frame.shape[:2]
    crop_size = min(w, h)
    x0 = (w - crop_size) // 2
    y0 = (h - crop_size) // 2
    square_frame = frame[y0:y0 + crop_size, x0:x0 + crop_size]

    cv2.imshow("Preview", square_frame)

    key = cv2.waitKey(1) & 0xFF

    # Esc starts recording
    if key == 27:
        print("Recording started.")
        break

# -------------------------
# Recording
# -------------------------
start = time.time()
frame_count = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Frame read failed during recording")
            break

        h, w = frame.shape[:2]
        crop_size = min(w, h)
        x0 = (w - crop_size) // 2
        y0 = (h - crop_size) // 2
        square_frame = frame[y0:y0 + crop_size, x0:x0 + crop_size]

        # Save clean frame, without REC text
        out.write(square_frame)

        # Show REC text only in the preview window
        preview_frame = square_frame.copy()

        cv2.putText(
            preview_frame,
            "REC",
            (15, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 0, 255),
            3,
            cv2.LINE_AA
        )

        sttime = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        log_file.write(f"{frame_count}\t{sttime}\n")

        frame_count += 1

        cv2.imshow("Preview", preview_frame)

        key = cv2.waitKey(1) & 0xFF

        # q or Esc stops recording
        if key == ord("q") or key == 27:
            print("Recording stopped.")
            break

except KeyboardInterrupt:
    print("Stopped by Ctrl+C")

finally:
    elapsed = time.time() - start

    cap.release()
    out.release()
    log_file.close()
    cv2.destroyAllWindows()

    measured_fps = frame_count / elapsed if elapsed > 0 else 0

    print("Elapsed seconds:", elapsed)
    print("Frames saved:", frame_count)
    print("Measured capture FPS:", measured_fps)
    print("Expected video duration:", frame_count / save_fps if save_fps > 0 else 0)