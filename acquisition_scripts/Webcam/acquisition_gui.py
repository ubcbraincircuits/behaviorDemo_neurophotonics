import cv2
import time
import os
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class AcquisitionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Webcam Acquisition GUI")
        self.root.geometry("520x430")

        # Camera / recording state
        self.cap = None
        self.out = None
        self.log_file = None
        self.capture_lock = threading.Lock()
        self.preview_thread = None
        self.record_thread = None
        self.preview_running = False
        self.recording = False
        self.stop_event = threading.Event()

        # Tkinter variables
        self.camera_index = tk.IntVar(value=0)
        self.width_var = tk.IntVar(value=1080)
        self.height_var = tk.IntVar(value=720)
        self.fps_var = tk.IntVar(value=30)
        self.mouse_name_var = tk.StringVar(value="mouse1")
        self.save_dir_var = tk.StringVar(value=os.path.abspath("recordings"))
        self.square_crop_var = tk.BooleanVar(value=True)

        self.status_var = tk.StringVar(value="Ready.")
        self.actual_camera_var = tk.StringVar(value="Actual camera: not opened yet")

        self.build_gui()
        self.add_instant_apply_traces()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # -------------------------
    # GUI layout
    # -------------------------
    def build_gui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        config = ttk.LabelFrame(main, text="Capture configuration", padding=10)
        config.pack(fill="x", pady=(0, 10))

        ttk.Label(config, text="Camera index:").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Spinbox(config, from_=0, to=10, textvariable=self.camera_index, width=10).grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(config, text="Width:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Spinbox(config, from_=160, to=4096, increment=10, textvariable=self.width_var, width=10).grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(config, text="Height:").grid(row=1, column=2, sticky="w", padx=(18, 0), pady=4)
        ttk.Spinbox(config, from_=120, to=2160, increment=10, textvariable=self.height_var, width=10).grid(row=1, column=3, sticky="w", pady=4)

        ttk.Label(config, text="FPS:").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Spinbox(config, from_=1, to=240, increment=1, textvariable=self.fps_var, width=10).grid(row=2, column=1, sticky="w", pady=4)

        ttk.Checkbutton(config, text="Center-crop to square", variable=self.square_crop_var).grid(row=2, column=2, columnspan=2, sticky="w", padx=(18, 0), pady=4)

        save = ttk.LabelFrame(main, text="Save settings", padding=10)
        save.pack(fill="x", pady=(0, 10))

        ttk.Label(save, text="Mouse name:").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(save, textvariable=self.mouse_name_var, width=24).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(save, text="Save folder:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(save, textvariable=self.save_dir_var).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Button(save, text="Browse...", command=self.browse_save_folder).grid(row=1, column=2, padx=(8, 0), pady=4)
        save.columnconfigure(1, weight=1)

        buttons = ttk.LabelFrame(main, text="Controls", padding=10)
        buttons.pack(fill="x", pady=(0, 10))

        ttk.Button(buttons, text="Preview", command=self.start_preview).grid(row=0, column=0, padx=4, pady=4)
        ttk.Button(buttons, text="Close preview", command=self.stop_preview).grid(row=0, column=1, padx=4, pady=4)
        ttk.Button(buttons, text="Record", command=lambda: self.start_recording(show_preview=False)).grid(row=0, column=2, padx=4, pady=4)
        ttk.Button(buttons, text="Record with preview", command=lambda: self.start_recording(show_preview=True)).grid(row=0, column=3, padx=4, pady=4)
        ttk.Button(buttons, text="Stop recording", command=self.stop_recording).grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=4)

        info = ttk.LabelFrame(main, text="Status", padding=10)
        info.pack(fill="both", expand=True)

        ttk.Label(info, textvariable=self.status_var, wraplength=460).pack(anchor="w")
        ttk.Label(info, textvariable=self.actual_camera_var, wraplength=460).pack(anchor="w", pady=(8, 0))
        ttk.Label(
            info,
            text="Preview window controls: press q or Esc to close preview/stop recording.",
            wraplength=460,
        ).pack(anchor="w", pady=(8, 0))

    def add_instant_apply_traces(self):
        # Whenever camera settings change, apply them to the live camera immediately.
        # This affects preview immediately. During recording, resolution/FPS changes are ignored
        # because changing frame size mid-file can corrupt the saved video.
        for var in (self.camera_index, self.width_var, self.height_var, self.fps_var):
            var.trace_add("write", lambda *args: self.apply_settings_if_camera_open())

    # -------------------------
    # Camera helpers
    # -------------------------
    def open_camera_if_needed(self):
        with self.capture_lock:
            desired_index = int(self.camera_index.get())

            if self.cap is not None and self.cap.isOpened():
                return True

            # CAP_MSMF is usually stable on Windows. If it fails, try default backend.
            self.cap = cv2.VideoCapture(desired_index, cv2.CAP_MSMF)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(desired_index)

            if not self.cap.isOpened():
                self.status_var.set("Could not open camera.")
                return False

            self.apply_camera_settings_locked()
            return True

    def apply_settings_if_camera_open(self):
        if self.recording:
            self.status_var.set("Recording is active. Stop recording before changing camera size/FPS.")
            return

        with self.capture_lock:
            if self.cap is not None and self.cap.isOpened():
                self.apply_camera_settings_locked()

    def apply_camera_settings_locked(self):
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            fps = int(self.fps_var.get())
        except tk.TclError:
            return

        # If camera index changed, reopen camera.
        current_index = int(self.camera_index.get())

        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)

        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.actual_camera_var.set(f"Actual camera: {actual_w} x {actual_h}, reported FPS: {actual_fps:.2f}")
        self.status_var.set("Camera settings applied.")

    def read_frame(self):
        with self.capture_lock:
            if self.cap is None or not self.cap.isOpened():
                return False, None
            return self.cap.read()

    def crop_frame_if_needed(self, frame):
        if not self.square_crop_var.get():
            return frame

        h, w = frame.shape[:2]
        crop_size = min(w, h)
        x0 = (w - crop_size) // 2
        y0 = (h - crop_size) // 2
        return frame[y0:y0 + crop_size, x0:x0 + crop_size]

    def release_camera_if_idle(self):
        if self.preview_running or self.recording:
            return
        with self.capture_lock:
            if self.cap is not None:
                self.cap.release()
                self.cap = None

    # -------------------------
    # Preview
    # -------------------------
    def start_preview(self):
        if self.recording:
            messagebox.showinfo("Recording active", "Use 'Record with preview' when starting a recording if you want a live preview.")
            return
        if self.preview_running:
            return
        if not self.open_camera_if_needed():
            messagebox.showerror("Camera error", "Could not open camera.")
            return

        self.stop_event.clear()
        self.preview_running = True
        self.preview_thread = threading.Thread(target=self.preview_loop, daemon=True)
        self.preview_thread.start()
        self.status_var.set("Preview started.")

    def preview_loop(self):
        last_time = time.time()
        fps_display = 0.0

        while self.preview_running and not self.stop_event.is_set():
            ret, frame = self.read_frame()
            if not ret:
                self.root.after(0, self.status_var.set, "Frame read failed during preview.")
                break

            frame = self.crop_frame_if_needed(frame)

            now = time.time()
            dt = now - last_time
            last_time = now
            if dt > 0:
                fps_display = 0.9 * fps_display + 0.1 * (1.0 / dt) if fps_display > 0 else (1.0 / dt)

            preview_frame = frame.copy()
            cv2.putText(
                preview_frame,
                f"FPS: {fps_display:.1f}",
                (15, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            cv2.imshow("Preview", preview_frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27 or cv2.getWindowProperty("Preview", cv2.WND_PROP_VISIBLE) < 1:
                break

        self.preview_running = False
        cv2.destroyWindow("Preview")
        self.release_camera_if_idle()
        self.root.after(0, self.status_var.set, "Preview closed.")

    def stop_preview(self):
        self.preview_running = False
        cv2.destroyWindow("Preview")
        self.release_camera_if_idle()

    # -------------------------
    # Recording
    # -------------------------
    def start_recording(self, show_preview=False):
        if self.recording:
            return

        mouse_name = self.mouse_name_var.get().strip()
        if mouse_name == "":
            messagebox.showerror("Missing mouse name", "Mouse name cannot be empty.")
            return

        save_root = self.save_dir_var.get().strip()
        if save_root == "":
            messagebox.showerror("Missing save folder", "Please choose a save folder.")
            return

        # Stop standalone preview before recording, so only one loop reads the camera.
        self.stop_preview()

        if not self.open_camera_if_needed():
            messagebox.showerror("Camera error", "Could not open camera.")
            return

        ret, test_frame = self.read_frame()
        if not ret:
            messagebox.showerror("Camera error", "Could not read from camera.")
            return

        test_frame = self.crop_frame_if_needed(test_frame)
        h, w = test_frame.shape[:2]

        session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_folder = os.path.join(save_root, mouse_name)
        os.makedirs(save_folder, exist_ok=True)

        video_path = os.path.join(save_folder, f"{mouse_name}_{session_time}.avi")
        timestamp_path = os.path.join(save_folder, f"{mouse_name}_{session_time}_timestamps.txt")

        save_fps = int(self.fps_var.get())
        if save_fps <= 0:
            save_fps = 30

        self.out = cv2.VideoWriter(
            video_path,
            cv2.VideoWriter_fourcc(*"MJPG"),
            save_fps,
            (w, h),
        )

        if not self.out.isOpened():
            self.out = None
            messagebox.showerror("VideoWriter error", "Could not open VideoWriter.")
            return

        self.log_file = open(timestamp_path, "w", encoding="utf-8")
        self.log_file.write("frame\ttime\n")

        self.recording = True
        self.stop_event.clear()
        self.record_thread = threading.Thread(
            target=self.record_loop,
            args=(show_preview, video_path, timestamp_path, save_fps),
            daemon=True,
        )
        self.record_thread.start()
        self.status_var.set(f"Recording started: {video_path}")

    def record_loop(self, show_preview, video_path, timestamp_path, save_fps):
        start = time.time()
        frame_count = 0
        fps_display = 0.0
        last_time = time.time()

        try:
            while self.recording and not self.stop_event.is_set():
                ret, frame = self.read_frame()
                if not ret:
                    self.root.after(0, self.status_var.set, "Frame read failed during recording.")
                    break

                frame = self.crop_frame_if_needed(frame)

                # Save clean frame only. No REC text or FPS is written to disk.
                self.out.write(frame)

                sttime = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                self.log_file.write(f"{frame_count}\t{sttime}\n")
                frame_count += 1

                if show_preview:
                    now = time.time()
                    dt = now - last_time
                    last_time = now
                    if dt > 0:
                        fps_display = 0.9 * fps_display + 0.1 * (1.0 / dt) if fps_display > 0 else (1.0 / dt)

                    preview_frame = frame.copy()
                    cv2.putText(
                        preview_frame,
                        "REC",
                        (15, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.2,
                        (0, 0, 255),
                        3,
                        cv2.LINE_AA,
                    )
                    cv2.putText(
                        preview_frame,
                        f"FPS: {fps_display:.1f}",
                        (15, 75),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA,
                    )

                    cv2.imshow("Preview", preview_frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q") or key == 27 or cv2.getWindowProperty("Preview", cv2.WND_PROP_VISIBLE) < 1:
                        break

        finally:
            elapsed = time.time() - start
            measured_fps = frame_count / elapsed if elapsed > 0 else 0
            expected_duration = frame_count / save_fps if save_fps > 0 else 0

            self.recording = False

            if self.out is not None:
                self.out.release()
                self.out = None
            if self.log_file is not None:
                self.log_file.close()
                self.log_file = None

            cv2.destroyWindow("Preview")
            self.release_camera_if_idle()

            message = (
                "Recording stopped.\n"
                f"Video: {video_path}\n"
                f"Timestamps: {timestamp_path}\n"
                f"Frames saved: {frame_count}\n"
                f"Measured capture FPS: {measured_fps:.2f}\n"
                f"Expected video duration: {expected_duration:.2f} s"
            )
            self.root.after(0, self.status_var.set, message)

    def stop_recording(self):
        self.recording = False
        self.stop_event.set()

    # -------------------------
    # Save folder / closing
    # -------------------------
    def browse_save_folder(self):
        folder = filedialog.askdirectory(initialdir=self.save_dir_var.get())
        if folder:
            self.save_dir_var.set(folder)

    def on_close(self):
        self.preview_running = False
        self.recording = False
        self.stop_event.set()
        time.sleep(0.1)

        with self.capture_lock:
            if self.cap is not None:
                self.cap.release()
                self.cap = None

        if self.out is not None:
            self.out.release()
        if self.log_file is not None:
            self.log_file.close()

        cv2.destroyAllWindows()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AcquisitionGUI(root)
    root.mainloop()
