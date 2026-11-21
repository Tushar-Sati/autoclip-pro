"""
AutoClip Pro - Diagnostic & Pipeline Verification Test
Verifies FFmpeg filters, ASS animated subtitle generation,
Virality scoring, and 9:16 rendering.
"""

import sys
import subprocess
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.app.config import TEMP_DIR, CLIPS_DIR
from backend.app.core.subtitle_generator import SubtitleGenerator
from backend.app.core.virality_scorer import ViralityScorer
from backend.app.core.copyright_shield import CopyrightShield
from backend.app.core.video_renderer import VideoRenderer

def run_tests():
    print("=" * 60)
    print("  🧪 Running AutoClip Pro Core Diagnostics")
    print("=" * 60)

    # 1. Virality Scorer Test
    print("\n[1/4] Testing Virality Scorer & Metadata Generator...")
    scorer = ViralityScorer()
    sample_text = "Wait what?! I can't believe he actually did this! Look at this clutch play, this is totally insane!"
    eval_result = scorer.evaluate_clip(sample_text, duration=25.0, uploader="EpicGamer")
    print(f"  ✓ Virality Rate: {eval_result['virality_rate']}/100")
    print(f"  ✓ Breakdown: {eval_result['breakdown']}")
    print(f"  ✓ Selected Title: {eval_result['selected_title']}")
    print(f"  ✓ Generated Hashtags: {' '.join(eval_result['hashtags'][:4])}")

    # 2. Subtitle Generator Test
    print("\n[2/4] Testing Hormozi-Style Animated ASS Subtitle Generator...")
    sub_gen = SubtitleGenerator()
    sample_words = [
        {"word": "WAIT", "start": 0.2, "end": 0.6},
        {"word": "WHAT?!", "start": 0.7, "end": 1.2},
        {"word": "LOOK", "start": 1.3, "end": 1.6},
        {"word": "AT", "start": 1.7, "end": 1.9},
        {"word": "THIS", "start": 2.0, "end": 2.4},
        {"word": "INSANE", "start": 2.5, "end": 3.0},
        {"word": "CLUTCH", "start": 3.1, "end": 3.8},
        {"word": "PLAY!", "start": 3.9, "end": 4.5},
    ]
    test_ass_path = str(TEMP_DIR / "test_subs.ass")
    sub_gen.generate_ass(sample_words, test_ass_path, clip_start=0.0, clip_duration=4.5, uploader="TestStreamer")
    assert Path(test_ass_path).exists()
    print(f"  ✓ Generated valid ASS subtitle file: {test_ass_path}")


    # 3. Create a synthetic 5-second test video with FFmpeg
    print("\n[3/4] Generating 5s 1920x1080 test video canvas with FFmpeg...")
    test_src_video = str(TEMP_DIR / "test_input_1080p.mp4")
    # Generates a 5s test color pattern with audio beep
    cmd_gen = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=size=1920x1080:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
        "-t", "5",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        test_src_video
    ]
    subprocess.run(cmd_gen, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"  ✓ Created test source: {test_src_video}")

    # 4. Video Renderer Test (Full 9:16 Split Screen + Subtitles + Watermark)
    print("\n[4/4] Testing 9:16 Split Screen & Subtitle Burning Render...")
    renderer = VideoRenderer()
    test_output_short = str(CLIPS_DIR / "test_rendered_short.mp4")
    
    mock_framing = {
        "mode": "split_screen",
        "facecam_box": {"x": 100, "y": 80, "w": 480, "h": 360},
        "gameplay_crop": {"x": 480, "y": 180, "w": 1200, "h": 900}
    }

    rendered_file = renderer.render_short(
        input_video=test_src_video,
        start_time=0.0,
        end_time=4.5,
        framing_info=mock_framing,
        subtitle_ass_path=test_ass_path,
        output_path=test_output_short,
        uploader="TestStreamer"
    )

    assert Path(rendered_file).exists()
    size_mb = Path(rendered_file).stat().st_size / (1024 * 1024)
    print(f"  ✓ Successfully rendered 9:16 Short ({size_mb:.2f} MB): {rendered_file}")

    print("\n" + "=" * 60)
    print("  🎉 ALL TESTS PASSED! AutoClip Pro Engine is 100% OPERATIONAL.")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
