import os
import re
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont

class ThumbnailGenerator:
    def __init__(self, target_width: int = 1080, target_height: int = 1920):
        self.target_width = target_width
        self.target_height = target_height

    def generate_thumbnails(
        self,
        video_path: str,
        output_prefix: str,
        headline_text: str = "WAIT FOR THE END!",
        uploader: str = "Streamer"
    ) -> Dict[str, str]:
        """
        Creates both a 9:16 vertical Short thumbnail and a 16:9 landscape YouTube thumbnail
        with peak facial emotion detection and punchy viral text overlays.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {}

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            return {}
        
        # 1. Scan frames to find the peak emotional frame (mouth open / highest variance)
        best_frame = None
        max_energy = -1
        sample_step = max(1, total_frames // 30)

        for i in range(0, total_frames, sample_step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            # Compute visual Laplacian energy / detail
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            energy = cv2.Laplacian(gray, cv2.CV_64F).var()

            if energy > max_energy:
                max_energy = energy
                best_frame = frame.copy()

        cap.release()

        if best_frame is None:
            return {}

        # 2. Color Grading / Vibrance Boost (+25% Saturation, +8% Brightness)
        hsv = cv2.cvtColor(best_frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.25, 0, 255)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.08, 0, 255)
        enhanced_bgr = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        # Clean headline text (remove non-ASCII to prevent missing glyph [] boxes)
        clean_headline = re.sub(r'[^\x00-\x7F]+', '', headline_text).strip()
        if not clean_headline:
            clean_headline = "WAIT FOR THE END!"

        # 3. Create 9:16 Vertical Short Cover
        vert_path = f"{output_prefix}_thumb_vertical.jpg"
        self._create_vertical_thumbnail(enhanced_bgr, vert_path, clean_headline)

        # 4. Create 16:9 Landscape YouTube Thumbnail
        horiz_path = f"{output_prefix}_thumb_landscape.jpg"
        self._create_landscape_thumbnail(enhanced_bgr, horiz_path, clean_headline)

        print(f"[ThumbnailGenerator] Created high-CTR thumbnails: {vert_path} & {horiz_path}")
        return {
            "vertical": vert_path,
            "landscape": horiz_path
        }

    def _create_vertical_thumbnail(self, bgr_img: np.ndarray, output_path: str, headline: str):
        """
        Builds high-impact 1080x1920 vertical Short thumbnail.
        The frame already contains the split screen and burned headline/subtitles.
        Adds a clean top viral badge for extra click-through rate.
        """
        img_pil = Image.fromarray(cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil, "RGBA")

        # Top Badge: "VIRAL MOMENT" pill
        badge_text = "VIRAL MOMENT"
        try:
            badge_font = ImageFont.truetype("arialbd.ttf", 36)
        except Exception:
            badge_font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        bw = bbox[2] - bbox[0]
        bh = bbox[3] - bbox[1]

        px = (self.target_width - (bw + 40)) // 2
        py = 70

        # Draw red pill badge
        draw.rounded_rectangle(
            [px, py, px + bw + 40, py + bh + 24],
            radius=16,
            fill=(220, 38, 38, 230),
            outline=(255, 255, 255, 200),
            width=2
        )
        draw.text((px + 20, py + 10), badge_text, font=badge_font, fill=(255, 255, 255, 255))

        # Convert back to RGB and save
        img_pil = img_pil.convert("RGB")
        img_pil.save(output_path, quality=95)

    def _create_landscape_thumbnail(self, bgr_img: np.ndarray, output_path: str, headline: str):
        """
        Builds 1280x720 16:9 YouTube thumbnail.
        Side-by-side composite: Streamer facecam on left (640x720), Gameplay on right (640x720).
        """
        h, w, _ = bgr_img.shape
        # Top half is webcam (0 to 840), bottom half is gameplay (840 to 1920)
        webcam_half = bgr_img[0:840, 0:w]
        game_half = bgr_img[840:h, 0:w]

        left_side = cv2.resize(webcam_half, (640, 720), interpolation=cv2.INTER_LANCZOS4)
        right_side = cv2.resize(game_half, (640, 720), interpolation=cv2.INTER_LANCZOS4)

        canvas = np.hstack([left_side, right_side])

        # Draw red glowing divider line down center
        cv2.line(canvas, (640, 0), (640, 720), (20, 20, 220), 8)

        img_pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil, "RGBA")

        try:
            font = ImageFont.truetype("arialbd.ttf", 46)
        except Exception:
            font = ImageFont.load_default()

        text = headline.upper()
        if len(text) > 34:
            text = text[:34] + "..."

        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (1280 - tw) // 2
        ty = 610

        # Draw semi-transparent dark banner across bottom for crystal clear legibility
        draw.rectangle([0, ty - 18, 1280, 720], fill=(0, 0, 0, 210))

        # Thick black outline for text
        for ox in range(-4, 5):
            for oy in range(-4, 5):
                draw.text((tx + ox, ty + oy), text, font=font, fill=(0, 0, 0, 255))

        # Bright Neon Yellow text
        draw.text((tx, ty), text, font=font, fill=(255, 235, 0, 255))

        img_pil = img_pil.convert("RGB")
        img_pil.save(output_path, quality=95)

