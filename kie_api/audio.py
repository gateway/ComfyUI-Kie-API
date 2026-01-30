"""Audio input helpers."""

import wave
from io import BytesIO
from pathlib import Path
from typing import Any


def _coerce_audio_to_wav_bytes(audio: Any) -> tuple[bytes, str]:
    """Coerce ComfyUI AUDIO input into WAV bytes for upload."""
    if isinstance(audio, (bytes, bytearray)):
        return bytes(audio), "bytes"

    if isinstance(audio, str):
        try:
            return Path(audio).read_bytes(), f"path:{audio}"
        except OSError as exc:
            raise RuntimeError(f"Failed to read audio file: {exc}") from exc

    if isinstance(audio, dict):
        audio_path = audio.get("path") or audio.get("filename") or audio.get("file")
        if isinstance(audio_path, str):
            try:
                return Path(audio_path).read_bytes(), f"dict_path:{audio_path}"
            except OSError as exc:
                raise RuntimeError(f"Failed to read audio file: {exc}") from exc

        waveform = audio.get("waveform")
        sample_rate = audio.get("sample_rate")
        if waveform is not None and sample_rate is not None:
            try:
                return _waveform_to_wav_bytes(waveform, int(sample_rate)), "waveform"
            except Exception as exc:
                raise RuntimeError(f"Failed to encode audio waveform: {exc}") from exc

    raise RuntimeError("audio input must be bytes, a file path string, or a dict with a path or waveform.")


def _waveform_to_wav_bytes(waveform, sample_rate: int) -> bytes:
    """Encode a waveform tensor/array as 16-bit PCM WAV bytes."""
    try:
        import numpy as np
    except Exception as exc:
        raise RuntimeError("numpy is required to encode audio waveforms.") from exc

    data = waveform
    if hasattr(data, "detach"):
        data = data.detach().cpu().numpy()
    else:
        data = np.asarray(data)

    if data.ndim == 1:
        data = data[None, :]
    if data.ndim == 3:
        # Handle [B, C, T] or [B, T, C]
        if data.shape[0] == 1:
            data = data[0]
        else:
            data = data[0]
        if data.ndim == 2 and data.shape[0] <= 8 and data.shape[1] > data.shape[0]:
            # likely [C, T]
            data = data
    if data.ndim == 2:
        # Normalize to [T, C]
        if data.shape[0] <= 8 and data.shape[1] > data.shape[0]:
            # likely [C, T]
            data = data.transpose(1, 0)
    if data.ndim != 2:
        raise RuntimeError("waveform must be 1D or 2D.")

    data = np.clip(data, -1.0, 1.0)
    pcm = (data * 32767.0).astype("<i2")

    with BytesIO() as buffer:
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(pcm.shape[1])
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm.tobytes())
        return buffer.getvalue()
