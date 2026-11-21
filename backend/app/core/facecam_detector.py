import cv2
import numpy as np
from typing import Dict, Any, Optional, Tuple

class FacecamDetector:
    def __init__(self, target_width: int = 1080, target_height: int = 1920):
        self.target_width = target_width
        self.target_height = target_height
        self.half_height = target_height // 2 # 960

    def analyze_video(self, video_path: str, sample_frames: int = 90) -> Dict[str, Any]:
        """
        Samples frames to detect if a streamer facecam exists,
        its bounding box coordinates, and optimal crop regions.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"has_facecam": False, "mode": "center_crop"}

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Use OpenCV's Haar Cascade or DNN face detector
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        detections = []
        step = max(1, total_frames // sample_frames)

        for i in range(0, total_frames, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))

            for (x, y, w, h) in faces:
                # Store face bounding box
                detections.append((x, y, w, h))

        cap.release()

        if not detections:
            print("[FacecamDetector] No face detected, falling back to center-focused 9:16 crop.")
            return {
                "has_facecam": False,
                "mode": "center_crop",
                "gameplay_crop": self._get_center_crop(frame_width, frame_height)
            }

        # Cluster detections to find the most consistent facecam position
        # Filter outliers by finding the median position
        xs = [d[0] for d in detections]
        ys = [d[1] for d in detections]
        ws = [d[2] for d in detections]
        hs = [d[3] for d in detections]

        med_x = int(np.median(xs))
        med_y = int(np.median(ys))
        med_w = int(np.median(ws))
        med_h = int(np.median(hs))

        # A facecam box is typically ~3.2x wider and 3.0x taller than just the detected face oval
        scale_x = 3.2
        scale_y = 3.0
        cam_w = int(med_w * scale_x)
        cam_h = int(med_h * scale_y)

        # Center expanded box around detected face
        cam_x = max(0, int(med_x - (cam_w - med_w) / 2))
        cam_y = max(0, int(med_y - (cam_h - med_h) / 2))

        # Ensure within frame limits
        cam_w = min(cam_w, frame_width - cam_x)
        cam_h = min(cam_h, frame_height - cam_y)

        # Gameplay crop (focused on center action of game)
        game_crop = self._get_gameplay_crop(frame_width, frame_height)

        print(f"[FacecamDetector] Detected Facecam box: x={cam_x}, y={cam_y}, w={cam_w}, h={cam_h}")
        return {
            "has_facecam": True,
            "mode": "split_screen",
            "facecam_box": {"x": cam_x, "y": cam_y, "w": cam_w, "h": cam_h},
            "gameplay_crop": game_crop,
            "orig_dimensions": {"width": frame_width, "height": frame_height}
        }

    def _get_center_crop(self, width: int, height: int) -> Dict[str, int]:
        """Calculates 9:16 center crop for non-gaming or talking head videos."""
        target_aspect = 9 / 16
        crop_width = int(height * target_aspect)
        if crop_width > width:
            crop_width = width
            crop_height = int(width / target_aspect)
            crop_x = 0
            crop_y = (height - crop_height) // 2
        else:
            crop_height = height
            crop_x = (width - crop_width) // 2
            crop_y = 0
        return {"x": crop_x, "y": crop_y, "w": crop_width, "h": crop_height}

    def _get_gameplay_crop(self, width: int, height: int) -> Dict[str, int]:
        """Calculates centered crop of gameplay for split screen."""
        # For the bottom half (1080x960), we want the action in the center
        crop_w = int(width * 0.75)
        crop_h = int(crop_w * (960 / 1080))
        crop_x = (width - crop_w) // 2
        crop_y = (height - crop_h) // 2
        return {"x": crop_x, "y": crop_y, "w": crop_w, "h": crop_h}
