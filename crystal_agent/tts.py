from __future__ import annotations
import io, logging, threading, wave
import numpy as np

class SpeechEngine:
    """Lazy Phonon TTS; model loading is deferred until the first spoken response."""
    def __init__(self, logger: logging.Logger):
        self.log = logger; self.model = None; self.processor = None; self.voice_latents = None
        self.model_id = None; self.lock = threading.Lock()

    def _load(self, model_id: str, device: str = "auto"):
        if self.model is not None and self.model_id == model_id: return
        from transformers import AutoProcessor, AutoModelForTextToWaveform
        from huggingface_hub import hf_hub_download
        from safetensors.torch import load_file
        self.log.info("Loading local TTS model: %s (first load can take a while)", model_id)
        self.processor = AutoProcessor.from_pretrained(model_id)
        kwargs = {"device_map": "auto"} if device == "auto" else {"device_map": device}
        self.model = AutoModelForTextToWaveform.from_pretrained(model_id, **kwargs)
        voice_path = hf_hub_download(model_id, "default-voice.safetensors")
        self.voice_latents = load_file(voice_path)["speaker_wavs"][0].T.float()
        self.model.eval(); self.model_id = model_id
        self.log.info("TTS model loaded")

    def synthesize(self, text: str, model_id: str, speed: float = 1.0, device: str = "auto") -> bytes:
        import torch
        with self.lock:
            self._load(model_id, device)
            conversation = [{"role": "user", "content": [{"type": "audio"}, {"type": "text", "text": text}]}]
            inputs = self.processor.apply_chat_template(conversation, tokenize=True, return_dict=True,
                add_generation_prompt=True, processor_kwargs={"audio_prompt_latents": [self.voice_latents]}).to(self.model.device)
            with torch.inference_mode():
                outputs = self.model.generate(**inputs)
                audio = self.processor.decode(outputs.audio_latents, outputs.audio_latents_mask)
            if isinstance(audio, (list, tuple)): audio = audio[0]
            if hasattr(audio, "detach"): audio = audio.detach().float().cpu().numpy()
            samples = np.asarray(audio, dtype=np.float32).squeeze()
            if samples.size == 0: raise RuntimeError("TTS returned an empty waveform")
            if speed != 1.0:
                length = max(1, int(samples.size / max(0.5, min(2.0, speed))))
                samples = np.interp(np.linspace(0, samples.size - 1, length), np.arange(samples.size), samples).astype(np.float32)
            pcm = (np.clip(samples, -1, 1) * 32767).astype("<i2")
            out = io.BytesIO()
            with wave.open(out, "wb") as f:
                f.setnchannels(1); f.setsampwidth(2); f.setframerate(24000); f.writeframes(pcm.tobytes())
            return out.getvalue()

def play_wav(wav_bytes: bytes, logger: logging.Logger):
    try:
        import sounddevice as sd
        with wave.open(io.BytesIO(wav_bytes), "rb") as w:
            frames = w.readframes(w.getnframes()); rate = w.getframerate(); channels = w.getnchannels()
        data = np.frombuffer(frames, dtype="<i2").astype(np.float32) / 32768.0
        if channels > 1: data = data.reshape(-1, channels)
        sd.play(data, rate); sd.wait()
    except Exception as e:
        logger.exception("Audio playback failed: %s", e)
        raise RuntimeError(f"Audio playback failed. Check sounddevice/audio output: {e}") from e
