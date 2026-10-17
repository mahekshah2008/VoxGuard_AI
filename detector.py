"""
VoxGuard AI - Audio Authenticity Detection Module

A rule-based audio forensics tool that analyzes WAV files for quality
and anomalies. Does NOT use machine learning or claim to detect
AI-generated speech. Returns Inconclusive for authenticity when no
validated detector is available.

Usage:
    from detector import AudioAuthenticator
    auth = AudioAuthenticator()
    result = auth.analyze("path/to/file.wav")
    print(result["classification"])
"""

from __future__ import annotations

import wave
from pathlib import Path
from typing import Any

import numpy as np
from scipy import signal

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_DURATION_S = 0.5
MIN_SAMPLE_RATE = 8000
CLIPPING_THRESHOLD = 0.99
SILENCE_RATIO_THRESHOLD = 0.95
MIN_SNR_DB = 10.0
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

FRAME_SIZE_S = 0.025
HOP_SIZE_S = 0.010


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class VoxGuardError(Exception):
    """Base exception for VoxGuard AI."""


class InvalidAudioError(VoxGuardError):
    """File is not a valid WAV or cannot be read."""


class UnsupportedFormatError(VoxGuardError):
    """WAV format is not supported."""


class CorruptedAudioError(VoxGuardError):
    """WAV file is corrupted or truncated."""


# ---------------------------------------------------------------------------
# WAV Reading
# ---------------------------------------------------------------------------


def read_wav_file(file_path: str) -> tuple[np.ndarray, int, int, int]:
    """Read a WAV file safely and return (samples, sample_rate, channels, bit_depth).

    Samples are normalized to float64 in [-1, 1] and converted to mono.
    Supports PCM (via wave module) and A-law/mu-law (via manual parsing).

    Raises:
        InvalidAudioError: File missing, empty, or not a valid WAV.
        UnsupportedFormatError: Unsupported sample width or channel count.
        CorruptedAudioError: Data is truncated or malformed.
    """
    path = Path(file_path)

    if not path.exists():
        raise InvalidAudioError(f"File not found: {file_path}")
    if not path.is_file():
        raise InvalidAudioError(f"Not a regular file: {file_path}")

    file_size = path.stat().st_size
    if file_size == 0:
        raise InvalidAudioError("File is empty (0 bytes)")
    if file_size > MAX_FILE_SIZE_BYTES:
        raise InvalidAudioError(
            f"File too large: {file_size / 1e6:.1f} MB (max {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB)"
        )

    # Try PCM via wave module first
    try:
        with wave.open(str(path), "rb") as wf:
            n_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()

            if n_channels < 1 or n_channels > 2:
                raise UnsupportedFormatError(f"Unsupported channel count: {n_channels}")
            if sample_width not in (1, 2, 3, 4):
                raise UnsupportedFormatError(f"Unsupported sample width: {sample_width} bytes")
            if sample_rate < 1:
                raise UnsupportedFormatError(f"Invalid sample rate: {sample_rate}")
            if n_frames < 1:
                raise CorruptedAudioError("WAV contains no audio frames")

            raw_data = wf.readframes(n_frames)
            expected = n_frames * n_channels * sample_width
            if len(raw_data) < expected:
                raise CorruptedAudioError(
                    f"Truncated data: got {len(raw_data)} bytes, expected {expected}"
                )

        samples = _bytes_to_float(raw_data, sample_width, n_channels)
        return samples, sample_rate, n_channels, sample_width * 8

    except wave.Error as e:
        error_msg = str(e)
        # Check if this is an A-law or mu-law file that we can handle manually
        if "unknown format: 6" in error_msg or "unknown format: 7" in error_msg:
            return _read_wav_alaw_mulaw(path)
        raise InvalidAudioError(f"Invalid WAV: {e}")


def _read_wav_alaw_mulaw(path: Path) -> tuple[np.ndarray, int, int, int]:
    """Manually parse an A-law or mu-law WAV file.

    Returns (samples, sample_rate, channels, bit_depth).
    """
    with open(path, "rb") as f:
        # Read RIFF header
        riff = f.read(4)
        if riff != b"RIFF":
            raise InvalidAudioError("Not a valid WAV file (missing RIFF header)")

        f.read(4)  # File size (skip)

        wave_id = f.read(4)
        if wave_id != b"WAVE":
            raise InvalidAudioError("Not a valid WAV file (missing WAVE identifier)")

        # Parse chunks
        fmt_found = False
        audio_format = None
        n_channels = None
        sample_rate = None
        raw_data = None

        while True:
            chunk_id = f.read(4)
            if len(chunk_id) < 4:
                break

            chunk_size = int.from_bytes(f.read(4), "little")

            if chunk_id == b"fmt ":
                fmt_found = True
                fmt_data = f.read(chunk_size)
                audio_format = int.from_bytes(fmt_data[0:2], "little")
                n_channels = int.from_bytes(fmt_data[2:4], "little")
                sample_rate = int.from_bytes(fmt_data[4:8], "little")
            elif chunk_id == b"data":
                if not fmt_found:
                    raise InvalidAudioError("WAV data chunk appears before fmt chunk")
                raw_data = f.read(chunk_size)
                break
            else:
                f.read(chunk_size)  # Skip unknown chunks

        if not fmt_found:
            raise InvalidAudioError("WAV file missing fmt chunk")
        if raw_data is None:
            raise InvalidAudioError("WAV file missing data chunk")

        if audio_format not in (6, 7):
            raise UnsupportedFormatError(f"Unsupported WAV format code: {audio_format}")
        if n_channels < 1 or n_channels > 2:
            raise UnsupportedFormatError(f"Unsupported channel count: {n_channels}")
        if sample_rate < 1:
            raise UnsupportedFormatError(f"Invalid sample rate: {sample_rate}")

        # Decode
        if audio_format == 6:
            samples = _alaw_decode(raw_data)
        else:
            samples = _mulaw_decode(raw_data)

        if n_channels > 1:
            samples = samples.reshape(-1, n_channels).mean(axis=1)

        return samples, sample_rate, n_channels, 8


def _alaw_decode(raw: bytes) -> np.ndarray:
    """Decode A-law encoded bytes to normalized float64 array."""
    # Build lookup table
    table = np.zeros(256, dtype=np.float64)
    for i in range(256):
        # Invert every other bit
        alaw = i ^ 0x55

        # Extract sign, exponent, and mantissa
        sign = alaw & 0x80
        exponent = (alaw >> 4) & 0x07
        mantissa = alaw & 0x0F

        # Reconstruct the linear sample
        if exponent == 0:
            sample = (mantissa << 4) + 8
        else:
            sample = ((mantissa << 4) + 0x108) << (exponent - 1)

        # Apply sign and normalize to [-1, 1]
        if sign:
            sample = -sample

        table[i] = sample / 32768.0

    # Apply lookup table
    indices = np.frombuffer(raw, dtype=np.uint8)
    return table[indices]


def _mulaw_decode(raw: bytes) -> np.ndarray:
    """Decode mu-law encoded bytes to normalized float64 array."""
    # mu-law constants
    MU = 255.0
    BIAS = 132.0

    # Build lookup table
    table = np.zeros(256, dtype=np.float64)
    for i in range(256):
        # Invert all bits
        mulaw = ~i & 0xFF

        # Extract sign, exponent, and mantissa
        sign = mulaw & 0x80
        exponent = (mulaw >> 4) & 0x07
        mantissa = mulaw & 0x0F

        # Reconstruct the linear sample
        sample = ((mantissa << 3) + BIAS) << exponent
        sample = sample - BIAS

        # Apply sign and normalize to [-1, 1]
        if sign:
            sample = -sample

        table[i] = sample / 32768.0

    # Apply lookup table
    indices = np.frombuffer(raw, dtype=np.uint8)
    return table[indices]


def _bytes_to_float(raw: bytes, width: int, channels: int) -> np.ndarray:
    """Convert raw WAV bytes to normalized float64 mono array."""
    if width == 1:
        arr = np.frombuffer(raw, dtype=np.uint8).astype(np.float64)
        arr = (arr - 128.0) / 128.0
    elif width == 2:
        arr = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
        arr = arr / 32768.0
    elif width == 3:
        n = len(raw) // 3
        raw_arr = np.frombuffer(raw, dtype=np.uint8)[: n * 3].reshape(n, 3)
        arr = (
            raw_arr[:, 0].astype(np.int32)
            | (raw_arr[:, 1].astype(np.int32) << 8)
            | (raw_arr[:, 2].astype(np.int32) << 16)
        )
        arr = np.where(arr & 0x800000, arr | ~0xFFFFFF, arr).astype(np.float64)
        arr = arr / 8388608.0
    else:  # width == 4
        arr = np.frombuffer(raw, dtype=np.int32).astype(np.float64)
        arr = arr / 2147483648.0

    if channels > 1:
        arr = arr.reshape(-1, channels).mean(axis=1)
    return arr


# ---------------------------------------------------------------------------
# Feature Extraction
# ---------------------------------------------------------------------------


def extract_features(samples: np.ndarray, sample_rate: int) -> dict[str, float]:
    """Extract basic audio-quality features from normalized samples."""
    n = len(samples)
    duration = n / sample_rate

    rms = float(np.sqrt(np.mean(samples**2))) if n > 0 else 0.0
    peak = float(np.max(np.abs(samples))) if n > 0 else 0.0

    # Zero-crossing rate
    if n > 1:
        signs = np.sign(samples)
        signs[signs == 0] = 1
        zcr = float(np.mean(np.abs(np.diff(signs)) > 0))
    else:
        zcr = 0.0

    # Clipping ratio
    clip_ratio = float(np.mean(np.abs(samples) > CLIPPING_THRESHOLD)) if n > 0 else 0.0

    # Frame-based analysis
    frame_len = max(1, int(FRAME_SIZE_S * sample_rate))
    hop_len = max(1, int(HOP_SIZE_S * sample_rate))

    if n >= frame_len:
        n_frames = 1 + (n - frame_len) // hop_len
        frames = np.lib.stride_tricks.as_strided(
            samples,
            shape=(n_frames, frame_len),
            strides=(samples.strides[0] * hop_len, samples.strides[0]),
        )
        frame_rms = np.sqrt(np.mean(frames**2, axis=1))
    else:
        frame_rms = np.array([rms])

    # Silence ratio
    silence_thresh = max(rms * 0.01, 1e-10)
    silence_ratio = float(np.mean(frame_rms < silence_thresh))

    # Noise floor from quietest 20% of frames
    sorted_rms = np.sort(frame_rms)
    n_noise = max(1, len(sorted_rms) // 5)
    noise_rms = float(np.sqrt(np.mean(sorted_rms[:n_noise] ** 2)))
    noise_floor_db = float(20 * np.log10(max(noise_rms, 1e-10)))

    # SNR
    snr_db = float(20 * np.log10(max(rms, 1e-10)) - noise_floor_db) if noise_rms > 0 else 99.0

    # Dynamic range
    if len(frame_rms) > 1:
        db = 20 * np.log10(np.maximum(frame_rms, 1e-10))
        dyn_range = float(np.percentile(db, 95) - np.percentile(db, 10))
    else:
        dyn_range = 0.0

    # Spectral features via Welch
    if n >= 256:
        nperseg = min(2048, n)
        freqs, psd = signal.welch(samples, fs=sample_rate, nperseg=nperseg)
        psd_sum = float(np.sum(psd))

        if psd_sum > 0:
            centroid = float(np.sum(freqs * psd) / psd_sum)
            bandwidth = float(np.sqrt(np.sum(((freqs - centroid) ** 2) * psd) / psd_sum))
            cum = np.cumsum(psd)
            idx = min(int(np.searchsorted(cum, 0.85 * cum[-1])), len(freqs) - 1)
            rolloff = float(freqs[idx])
            psd_nz = psd[psd > 1e-20]
            flatness = float(np.exp(np.mean(np.log(psd_nz))) / np.mean(psd_nz)) if len(psd_nz) > 0 else 0.0
        else:
            centroid = bandwidth = rolloff = flatness = 0.0
    else:
        centroid = bandwidth = rolloff = flatness = 0.0

    return {
        "duration_seconds": round(duration, 3),
        "sample_rate": sample_rate,
        "rms_energy": round(rms, 6),
        "peak_amplitude": round(peak, 6),
        "zero_crossing_rate": round(zcr, 4),
        "clipping_ratio": round(clip_ratio, 6),
        "silence_ratio": round(silence_ratio, 4),
        "noise_floor_db": round(noise_floor_db, 1),
        "snr_db": round(snr_db, 1),
        "dynamic_range_db": round(dyn_range, 1),
        "spectral_centroid_hz": round(centroid, 1),
        "spectral_bandwidth_hz": round(bandwidth, 1),
        "spectral_rolloff_hz": round(rolloff, 1),
        "spectral_flatness": round(flatness, 4),
    }


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


def classify(features: dict[str, float]) -> tuple[str, list[str], str]:
    """Classify audio based on measured features.

    Returns (classification, triggered_rules, explanation).

    Without a validated deepfake detection model, authenticity is always
    Inconclusive. Quality issues are reported separately.
    """
    rules: list[str] = []

    # Quality gates
    if features["duration_seconds"] < MIN_DURATION_S:
        rules.append("DURATION_TOO_SHORT")
    if features["sample_rate"] < MIN_SAMPLE_RATE:
        rules.append("SAMPLE_RATE_TOO_LOW")
    if features["rms_energy"] < 1e-6:
        rules.append("ENTIRELY_SILENT")
    if features["silence_ratio"] > SILENCE_RATIO_THRESHOLD:
        rules.append("EXCESSIVE_SILENCE")
    if features["snr_db"] < MIN_SNR_DB:
        rules.append("LOW_SNR")

    # Anomaly indicators (quality issues, NOT proof of synthesis)
    if features["clipping_ratio"] > 0.01:
        rules.append("HEAVY_CLIPPING")
    if features["spectral_flatness"] > 0.9 or features["spectral_flatness"] < 0.01:
        rules.append("UNUSUAL_SPECTRAL_FLATNESS")
    if features["dynamic_range_db"] < 6.0:
        rules.append("LOW_DYNAMIC_RANGE")

    # Determine classification
    quality_issues = [r for r in rules if r != "HEAVY_CLIPPING" and r != "UNUSUAL_SPECTRAL_FLATNESS" and r != "LOW_DYNAMIC_RANGE"]
    anomaly_issues = [r for r in rules if r in ("HEAVY_CLIPPING", "UNUSUAL_SPECTRAL_FLATNESS", "LOW_DYNAMIC_RANGE")]

    if quality_issues:
        classification = "Inconclusive"
        explanation = (
            f"Audio quality is insufficient for reliable assessment. "
            f"Issues: {', '.join(quality_issues)}. "
            "No authenticity determination can be made."
        )
    elif len(anomaly_issues) >= 2:
        classification = "Suspicious"
        explanation = (
            f"Multiple anomalies detected: {', '.join(anomaly_issues)}. "
            "These are quality indicators only and do NOT prove the audio is synthetic. "
            "Independent verification is strongly recommended."
        )
    elif len(anomaly_issues) == 1:
        classification = "Inconclusive"
        explanation = (
            f"One anomaly detected: {anomaly_issues[0]}. "
            "Insufficient evidence for any authenticity determination."
        )
    else:
        classification = "Inconclusive"
        explanation = (
            "Audio quality is adequate, but no validated deepfake detection model is available. "
            "Authenticity cannot be determined from acoustic features alone."
        )

    return classification, rules, explanation


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------


class AudioAuthenticator:
    """Analyze WAV files for audio quality and authenticity indicators."""

    def analyze(self, file_path: str) -> dict[str, Any]:
        """Analyze a WAV file and return a structured result.

        Args:
            file_path: Path to a WAV file.

        Returns:
            Dictionary with keys: classification, risk_indicator, explanation,
            limitations, audio_quality, measured_features, triggered_rules,
            financial_verification_recommendation.

        Raises:
            VoxGuardError: If the file cannot be read or is invalid.
        """
        samples, sample_rate, n_channels, bit_depth = read_wav_file(file_path)
        features = extract_features(samples, sample_rate)
        classification, rules, explanation = classify(features)

        # Risk indicator (qualitative, no invented probabilities)
        if classification == "Suspicious":
            risk = "Medium"
        elif classification == "Likely Genuine":
            risk = "Low"
        else:
            risk = "Unknown"

        # Audio quality summary
        quality_issues = [r for r in rules if r not in ("HEAVY_CLIPPING", "UNUSUAL_SPECTRAL_FLATNESS", "LOW_DYNAMIC_RANGE")]
        audio_quality = {
            "adequate_for_assessment": len(quality_issues) == 0,
            "issues": quality_issues,
            "sample_rate": sample_rate,
            "duration_seconds": features["duration_seconds"],
            "bit_depth": bit_depth,
            "num_channels": n_channels,
        }

        # Limitations
        limitations = [
            "This tool uses rule-based audio forensics, not a validated AI deepfake detection model.",
            "Audio analysis cannot establish the identity of the speaker.",
            "Acoustic features alone cannot distinguish genuine from synthetic speech.",
            "This tool should not be used as the sole basis for security decisions.",
        ]
        if classification == "Inconclusive":
            limitations.append("A reliable authenticity assessment could not be made.")

        # Financial verification recommendation
        if classification == "Suspicious":
            fin_rec = (
                "This recording has been flagged as suspicious. Any financial instructions "
                "received via this audio should be independently verified through a separate, "
                "trusted channel before action is taken."
            )
        elif classification == "Likely Genuine":
            fin_rec = (
                "While no anomalies were detected, this does not guarantee authenticity. "
                "For sensitive financial instructions, independent verification through a "
                "separate trusted channel is still recommended."
            )
        else:
            fin_rec = (
                "A reliable assessment could not be made. Any financial instructions received "
                "via this audio should be independently verified through a separate, trusted "
                "channel before action is taken."
            )

        return {
            "classification": classification,
            "risk_indicator": risk,
            "explanation": explanation,
            "limitations": limitations,
            "audio_quality": audio_quality,
            "measured_features": features,
            "triggered_rules": rules,
            "financial_verification_recommendation": fin_rec,
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python detector.py <wav_file>")
        sys.exit(1)

    auth = AudioAuthenticator()
    try:
        result = auth.analyze(sys.argv[1])
        print(json.dumps(result, indent=2))
    except VoxGuardError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
