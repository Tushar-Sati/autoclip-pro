import cv2
import numpy as np
from typing import Dict, Any, Optional, Tuple

class FacecamDetector:
    def __init__(self, target_width: int = 1080, target_height: int = 1920):
        self.target_width = target_width
        self.target_height = target_height
        self.top_height = 840
        self.bottom_height = target_height - self.top_height # 1080

    def analyze_video(self, video_path: str, sample_frames: int = 60) -> Dict[str, Any]:
        """
        Detects persistent streamer facecam in 1080p footage,
        computes full-bleed top zoom crop and clean gameplay crop without duplicate webcam.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"has_facecam": False, "mode": "center_crop"}

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        detections = []
        step = max(1, total_frames // sample_frames)

        for i in range(0, total_frames, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(50, 50))

            for (x, y, w, h) in faces:
                detections.append((x, y, w, h))

        cap.release()

        if not detections:
            print("[FacecamDetector] No persistent face detected. Using center crop.")
            return {
                "has_facecam": False,
                "mode": "center_crop",
                "gameplay_crop": self._get_center_crop(frame_width, frame_height)
            }

        # Cluster detections by spatial proximity (streamer facecam remains in tight radius)
        clusters = []
        for d in detections:
            dx, dy, dw, dh = d
            dcx, dcy = dx + dw / 2, dy + dh / 2
            
            matched = False
            for c in clusters:
                if np.hypot(dcx - c['cx'], dcy - c['cy']) < 80: # within 80px
                    c['members'].append(d)
                    c['cx'] = np.mean([m[0] + m[2]/2 for m in c['members']])
                    c['cy'] = np.mean([m[1] + m[3]/2 for m in c['members']])
                    matched = True
                    break
            if not matched:
                clusters.append({'cx': dcx, 'cy': dcy, 'members': [d]})

        # The cluster with the most detections across time is the streamer facecam
        best_cluster = max(clusters, key=lambda c: len(c['members']))
        members = best_cluster['members']

        med_x = int(np.median([m[0] for m in members]))
        med_y = int(np.median([m[1] for m in members]))
        med_w = int(np.median([m[2] for m in members]))
        med_h = int(np.median([m[3] for m in members]))

        # Calculate Full-Bleed Streamer Webcam Crop (aspect ratio 1080 : top_height)
        target_aspect = self.target_width / float(self.top_height) # 1080 / 840 = ~1.286
        crop_h = int(med_h * 3.8) # Head + shoulders + chair + room
        crop_w = int(crop_h * target_aspect)

        # Center horizontally on streamer's face
        cam_x = int(med_x + med_w / 2 - crop_w / 2)
        # Face placed slightly above center (35% from top of webcam frame)
        cam_y = int(med_y - med_h * 0.6)

        # Clamp safely within source bounds
        cam_x = max(0, min(frame_width - crop_w, cam_x))
        cam_y = max(0, min(frame_height - crop_h, cam_y))
        cam_w = min(crop_w, frame_width - cam_x)
        cam_h = min(crop_h, frame_height - cam_y)

        # Gameplay Crop: Exclude the webcam quadrant so no duplicate mini-webcam appears in the gameplay!
        is_webcam_left = (med_x + med_w / 2) < (frame_width / 2)
        game_aspect = self.target_width / float(self.bottom_height) # 1080 / 1080 = 1.0 (square) or 9:16
        game_h = frame_height
        game_w = int(game_h * (1080 / 1080)) # 1080x1080 square action window

        if is_webcam_left:
            # Shift gameplay crop to the right to cleanly avoid streamer webcam box
            game_x = max(int(cam_x + cam_w * 0.8), int((frame_width - game_w) * 0.65))
        else:
            # Webcam on right, shift gameplay crop to left
            game_x = min(int(cam_x - game_w * 0.8), int((frame_width - game_w) * 0.35))

        game_x = max(0, min(frame_width - game_w, game_x))
        game_y = 0

        print(f"[FacecamDetector 1080p] Locked Streamer Webcam: x={cam_x}, y={cam_y}, w={cam_w}, h={cam_h}")
        print(f"[FacecamDetector 1080p] Clean Gameplay Window: x={game_x}, y={game_y}, w={game_w}, h={game_h}")

        return {
            "has_facecam": True,
            "mode": "split_screen",
            "top_height": self.top_height,
            "bottom_height": self.bottom_height,
            "facecam_box": {"x": cam_x, "y": cam_y, "w": cam_w, "h": cam_h},
            "gameplay_crop": {"x": game_x, "y": game_y, "w": game_w, "h": game_h},
            "orig_dimensions": {"width": frame_width, "height": frame_height}
        }


