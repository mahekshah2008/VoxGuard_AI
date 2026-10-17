"""
Tests for VoxGuard AI detector module.

These tests verify the structure and behavior of detector.py using
synthetic audio files. They do NOT validate deepfake detection accuracy.
"""

import shutil
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from detector import (
    AudioAuthenticator,
    CorruptedAudioError,
    InvalidAudioError,
    UnsupportedFormatError,
    VoxGuardError,
    classify,
    extract_features,
    read_wav_file,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_wav(path, samples, sample_rate=44100, n_channels=1, sample_width=2):
    """Write a WAV file from float samples in [-1, 1]."""
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        if sample_width == 2:
            int_samples = np.clip(samples * 32767, -32768, 32767).astype(np.int16)
            if n_channels > 1:
                int_samples = np.tile(int_samples, (n_channels, 1)).T.flatten()
            wf.writeframes(int_samples.tobytes())


def _tone(freq, duration, sample_rate=44100, amplitude=0.5):
    """Generate a sine wave."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return amplitude * np.sin(2 * np.pi * freq * t)


def _tone_with_envelope(freq, duration, sample_rate=44100):
    """Generate a tone with amplitude envelope for more speech-like variation."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    envelope = np.ones_like(t)
    attack = int(0.1 * sample_rate)
    release = int(0.1 * sample_rate)
    envelope[:attack] = np.linspace(0, 1, attack)
    envelope[-release:] = np.linspace(1, 0, release)
    return 0.5 * envelope * np.sin(2 * np.pi * freq * t)


def _silence(duration, sample_rate=44100):
    """Generate silence."""
    return np.zeros(int(sample_rate * duration))


# ---------------------------------------------------------------------------
# Tests: read_wav_file
# ---------------------------------------------------------------------------


class TestWavReading(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir, ignore_errors=True)

    def test_read_valid_mono_wav(self):
        path = Path(self.tmpdir) / "mono.wav"
        _write_wav(path, _tone(440, 1.0))
        audio, sr, ch, bd = read_wav_file(str(path))
        self.assertEqual(sr, 44100)
        self.assertEqual(ch, 1)
        self.assertEqual(bd, 16)
        self.assertIsInstance(audio, np.ndarray)

    def test_read_valid_stereo_wav(self):
        path = Path(self.tmpdir) / "stereo.wav"
        samples = _tone(440, 1.0)
        _write_wav(path, samples, n_channels=2)
        audio, sr, ch, bd = read_wav_file(str(path))
        self.assertEqual(ch, 2)
        self.assertEqual(len(audio), len(samples))

    def test_missing_file_raises_invalid(self):
        with self.assertRaises(InvalidAudioError):
            read_wav_file(str(Path(self.tmpdir) / "nonexistent.wav"))

    def test_empty_file_raises_invalid(self):
        path = Path(self.tmpdir) / "empty.wav"
        path.write_bytes(b"")
        with self.assertRaises(InvalidAudioError):
            read_wav_file(str(path))

    def test_non_wav_file_raises_invalid(self):
        path = Path(self.tmpdir) / "fake.wav"
        path.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")
        with self.assertRaises(InvalidAudioError):
            read_wav_file(str(path))

    def test_text_file_with_wav_extension_raises_invalid(self):
        path = Path(self.tmpdir) / "text.wav"
        path.write_text("This is not audio data")
        with self.assertRaises(InvalidAudioError):
            read_wav_file(str(path))


# ---------------------------------------------------------------------------
# Tests: extract_features
# ---------------------------------------------------------------------------


class TestFeatureExtraction(unittest.TestCase):
    def test_silence_features(self):
        features = extract_features(_silence(1.0), 44100)
        self.assertAlmostEqual(features["rms_energy"], 0.0, places=6)
        self.assertAlmostEqual(features["peak_amplitude"], 0.0, places=6)
        self.assertGreater(features["silence_ratio"], 0.99)

    def test_tone_features(self):
        features = extract_features(_tone(440, 1.0), 44100)
        self.assertGreater(features["rms_energy"], 0.1)
        self.assertGreater(features["peak_amplitude"], 0.3)
        self.assertLess(features["silence_ratio"], 0.1)
        self.assertGreater(features["spectral_centroid_hz"], 0)

    def test_all_expected_keys_present(self):
        features = extract_features(_tone(440, 1.0), 44100)
        expected = {
            "duration_seconds", "sample_rate", "rms_energy", "peak_amplitude",
            "zero_crossing_rate", "clipping_ratio", "silence_ratio",
            "noise_floor_db", "snr_db", "dynamic_range_db",
            "spectral_centroid_hz", "spectral_bandwidth_hz",
            "spectral_rolloff_hz", "spectral_flatness",
        }
        self.assertEqual(set(features.keys()), expected)

    def test_empty_samples(self):
        features = extract_features(np.array([]), 44100)
        self.assertEqual(features["rms_energy"], 0.0)
        self.assertEqual(features["duration_seconds"], 0.0)


# ---------------------------------------------------------------------------
# Tests: classify
# ---------------------------------------------------------------------------


class TestClassification(unittest.TestCase):
    def test_silence_classifies_inconclusive(self):
        features = {
            "duration_seconds": 1.0, "sample_rate": 44100,
            "rms_energy": 0.0, "peak_amplitude": 0.0,
            "zero_crossing_rate": 0.0, "clipping_ratio": 0.0,
            "silence_ratio": 1.0, "noise_floor_db": -100.0,
            "snr_db": 0.0, "dynamic_range_db": 0.0,
            "spectral_centroid_hz": 0.0, "spectral_bandwidth_hz": 0.0,
            "spectral_rolloff_hz": 0.0, "spectral_flatness": 0.0,
        }
        classification, rules, explanation = classify(features)
        self.assertEqual(classification, "Inconclusive")
        self.assertIn("ENTIRELY_SILENT", rules)

    def test_short_audio_classifies_inconclusive(self):
        features = {
            "duration_seconds": 0.1, "sample_rate": 44100,
            "rms_energy": 0.3, "peak_amplitude": 0.5,
            "zero_crossing_rate": 0.05, "clipping_ratio": 0.0,
            "silence_ratio": 0.1, "noise_floor_db": -40.0,
            "snr_db": 30.0, "dynamic_range_db": 20.0,
            "spectral_centroid_hz": 1000.0, "spectral_bandwidth_hz": 500.0,
            "spectral_rolloff_hz": 2000.0, "spectral_flatness": 0.3,
        }
        classification, rules, _ = classify(features)
        self.assertEqual(classification, "Inconclusive")
        self.assertIn("DURATION_TOO_SHORT", rules)

    def test_low_sample_rate_classifies_inconclusive(self):
        features = {
            "duration_seconds": 1.0, "sample_rate": 4000,
            "rms_energy": 0.3, "peak_amplitude": 0.5,
            "zero_crossing_rate": 0.05, "clipping_ratio": 0.0,
            "silence_ratio": 0.1, "noise_floor_db": -40.0,
            "snr_db": 30.0, "dynamic_range_db": 20.0,
            "spectral_centroid_hz": 1000.0, "spectral_bandwidth_hz": 500.0,
            "spectral_rolloff_hz": 2000.0, "spectral_flatness": 0.3,
        }
        classification, rules, _ = classify(features)
        self.assertEqual(classification, "Inconclusive")
        self.assertIn("SAMPLE_RATE_TOO_LOW", rules)

    def test_classify_returns_tuple_of_correct_types(self):
        features = {
            "duration_seconds": 1.0, "sample_rate": 44100,
            "rms_energy": 0.3, "peak_amplitude": 0.5,
            "zero_crossing_rate": 0.05, "clipping_ratio": 0.0,
            "silence_ratio": 0.1, "noise_floor_db": -40.0,
            "snr_db": 30.0, "dynamic_range_db": 20.0,
            "spectral_centroid_hz": 1000.0, "spectral_bandwidth_hz": 500.0,
            "spectral_rolloff_hz": 2000.0, "spectral_flatness": 0.3,
        }
        result = classify(features)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        self.assertIsInstance(result[0], str)
        self.assertIsInstance(result[1], list)
        self.assertIsInstance(result[2], str)


# ---------------------------------------------------------------------------
# Tests: AudioAuthenticator
# ---------------------------------------------------------------------------


class TestAudioAuthenticator(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir, ignore_errors=True)
        self.auth = AudioAuthenticator()

    def test_analyze_valid_wav_returns_dict(self):
        path = Path(self.tmpdir) / "valid.wav"
        _write_wav(path, _tone_with_envelope(440, 2.0))
        result = self.auth.analyze(str(path))
        self.assertIsInstance(result, dict)

    def test_analyze_result_has_all_required_keys(self):
        path = Path(self.tmpdir) / "valid.wav"
        _write_wav(path, _tone_with_envelope(440, 2.0))
        result = self.auth.analyze(str(path))
        required = {
            "classification", "risk_indicator", "explanation",
            "limitations", "audio_quality", "measured_features",
            "triggered_rules", "financial_verification_recommendation",
        }
        self.assertEqual(set(result.keys()), required)

    def test_analyze_missing_file_raises(self):
        with self.assertRaises(InvalidAudioError):
            self.auth.analyze(str(Path(self.tmpdir) / "missing.wav"))

    def test_analyze_invalid_file_raises(self):
        path = Path(self.tmpdir) / "invalid.wav"
        path.write_bytes(b"NOTAWAVFILE" * 100)
        with self.assertRaises(InvalidAudioError):
            self.auth.analyze(str(path))

    def test_analyze_silence_returns_inconclusive(self):
        path = Path(self.tmpdir) / "silence.wav"
        _write_wav(path, _silence(1.0))
        result = self.auth.analyze(str(path))
        self.assertEqual(result["classification"], "Inconclusive")
        self.assertIn("ENTIRELY_SILENT", result["triggered_rules"])

    def test_analyze_short_audio_returns_inconclusive(self):
        path = Path(self.tmpdir) / "short.wav"
        _write_wav(path, _tone(440, 0.1))
        result = self.auth.analyze(str(path))
        self.assertEqual(result["classification"], "Inconclusive")
        self.assertIn("DURATION_TOO_SHORT", result["triggered_rules"])

    def test_analyze_empty_file_raises(self):
        path = Path(self.tmpdir) / "empty.wav"
        path.write_bytes(b"")
        with self.assertRaises(InvalidAudioError):
            self.auth.analyze(str(path))

    def test_limitations_mention_no_validated_detector(self):
        path = Path(self.tmpdir) / "valid.wav"
        _write_wav(path, _tone_with_envelope(440, 2.0))
        result = self.auth.analyze(str(path))
        text = " ".join(result["limitations"]).lower()
        self.assertIn("not a validated", text)

    def test_financial_recommendation_present(self):
        path = Path(self.tmpdir) / "valid.wav"
        _write_wav(path, _tone_with_envelope(440, 2.0))
        result = self.auth.analyze(str(path))
        self.assertIn("financial", result["financial_verification_recommendation"].lower())

    def test_audio_quality_structure(self):
        path = Path(self.tmpdir) / "valid.wav"
        _write_wav(path, _tone_with_envelope(440, 2.0))
        result = self.auth.analyze(str(path))
        aq = result["audio_quality"]
        for key in ("adequate_for_assessment", "issues", "sample_rate",
                    "duration_seconds", "bit_depth", "num_channels"):
            self.assertIn(key, aq)

    def test_measured_features_structure(self):
        path = Path(self.tmpdir) / "valid.wav"
        _write_wav(path, _tone_with_envelope(440, 2.0))
        result = self.auth.analyze(str(path))
        mf = result["measured_features"]
        for key in ("rms_energy", "peak_amplitude", "clipping_ratio",
                    "silence_ratio", "snr_db"):
            self.assertIn(key, mf)

    def test_classification_is_valid_value(self):
        path = Path(self.tmpdir) / "valid.wav"
        _write_wav(path, _tone_with_envelope(440, 2.0))
        result = self.auth.analyze(str(path))
        self.assertIn(result["classification"],
                      ("Likely Genuine", "Suspicious", "Inconclusive"))

    def test_risk_indicator_is_valid_value(self):
        path = Path(self.tmpdir) / "valid.wav"
        _write_wav(path, _tone_with_envelope(440, 2.0))
        result = self.auth.analyze(str(path))
        self.assertIn(result["risk_indicator"], ("Low", "Medium", "High", "Unknown"))


# ---------------------------------------------------------------------------
# Tests: Exception hierarchy
# ---------------------------------------------------------------------------


class TestExceptionHierarchy(unittest.TestCase):
    def test_invalid_audio_is_voxguard_error(self):
        self.assertTrue(issubclass(InvalidAudioError, VoxGuardError))

    def test_unsupported_format_is_voxguard_error(self):
        self.assertTrue(issubclass(UnsupportedFormatError, VoxGuardError))

    def test_corrupted_audio_is_voxguard_error(self):
        self.assertTrue(issubclass(CorruptedAudioError, VoxGuardError))


if __name__ == "__main__":
    unittest.main()
