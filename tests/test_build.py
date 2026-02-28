"""Tests for build-related import verification and ONNX backend."""

import pytest


def test_onnxruntime_importable():
    """onnxruntime should be importable for basic-pitch inference."""
    import onnxruntime

    assert onnxruntime is not None


def test_basic_pitch_onnx_model_exists():
    """basic-pitch should ship the ONNX model file."""
    from basic_pitch import ONNX_PRESENT, FilenameSuffix, build_icassp_2022_model_path

    assert ONNX_PRESENT, "onnxruntime not detected by basic-pitch"
    model_path = build_icassp_2022_model_path(FilenameSuffix.onnx)
    assert model_path.exists(), f"ONNX model not found at {model_path}"


def test_basic_pitch_onnx_inference():
    """basic-pitch should be able to load the ONNX model."""
    from basic_pitch import ONNX_PRESENT

    if not ONNX_PRESENT:
        pytest.skip("onnxruntime not installed")

    from basic_pitch import FilenameSuffix, build_icassp_2022_model_path
    from basic_pitch.inference import Model

    model_path = build_icassp_2022_model_path(FilenameSuffix.onnx)
    model = Model(str(model_path))
    assert model.model_type == Model.MODEL_TYPES.ONNX


def test_key_imports_available():
    """All key runtime imports should be available."""
    import cv2
    import librosa
    import numpy
    import onnxruntime
    import pretty_midi
    import resampy
    import scipy
    import sklearn
    import soundfile
    import yt_dlp

    assert all([cv2, librosa, numpy, onnxruntime, pretty_midi, resampy, scipy, sklearn, soundfile, yt_dlp])
