"""Basic Synthesia video detection using frame analysis.

Looks for the characteristic Synthesia pattern: colored vertical bars
(falling notes) in the upper portion of the frame above a horizontal
piano keyboard strip at the bottom.

Best-effort — may miss some Synthesia videos or produce false positives.
Falls back to audio transcription silently.
"""

import cv2
import numpy as np


def detect_synthesia_pattern(frame: np.ndarray) -> bool:
    """Analyze a single video frame for the Synthesia visual pattern.

    Checks for:
    1. A bright horizontal band in the bottom ~15% (piano keyboard)
    2. Multiple narrow colored vertical regions in the upper portion (falling notes)

    Args:
        frame: BGR image as numpy array (height, width, 3).

    Returns:
        True if the frame matches the Synthesia pattern.
    """
    h, w = frame.shape[:2]
    if h < 100 or w < 100:
        return False

    # Check 1: Piano keyboard strip at the bottom
    bottom_strip = frame[int(h * 0.85) :, :]
    gray_bottom = cv2.cvtColor(bottom_strip, cv2.COLOR_BGR2GRAY)
    bright_pct = np.mean(gray_bottom > 180)
    if bright_pct < 0.20:
        return False

    # Check 2: Colored vertical bars in the upper portion
    upper_region = frame[int(h * 0.15) : int(h * 0.75), :]
    hsv = cv2.cvtColor(upper_region, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]

    # Count columns that have a significant run of saturated pixels
    col_saturation = np.mean(saturation > 100, axis=0)
    colored_columns = np.sum(col_saturation > 0.3)
    if colored_columns < 5:
        return False

    # Check 3: Columns should be narrow (note-like), not wide blocks
    is_colored = col_saturation > 0.3
    transitions = np.sum(np.diff(is_colored.astype(int)) != 0)
    return bool(transitions >= 8)


def check_video_for_synthesia(video_path: str, sample_count: int = 5) -> bool:
    """Sample frames from a video and check for Synthesia pattern.

    Args:
        video_path: Path to the video file.
        sample_count: Number of frames to sample.

    Returns:
        True if the majority of sampled frames match the Synthesia pattern.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return False

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames < sample_count:
        cap.release()
        return False

    detections = 0
    for i in range(sample_count):
        frame_pos = int(total_frames * (0.2 + 0.6 * i / max(sample_count - 1, 1)))
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
        ret, frame = cap.read()
        if ret and detect_synthesia_pattern(frame):
            detections += 1

    cap.release()
    return detections > sample_count // 2
