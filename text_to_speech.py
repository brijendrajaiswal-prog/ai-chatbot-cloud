from pathlib import Path
import time
import wave

from piper import PiperVoice

BASE_DIR = Path(__file__).resolve().parent
VOICE_DIR = BASE_DIR / "voices"
OUTPUT_DIR = BASE_DIR / "generated_audio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VOICE_MODELS = {
    "hi": VOICE_DIR / "hi_IN-pratham-medium.onnx",
    "en": VOICE_DIR / "en_US-amy-medium.onnx",
}

_loaded_voices = {}


def _get_voice(language: str) -> PiperVoice:
    language = "hi" if language.lower().startswith("hi") else "en"
    if language not in _loaded_voices:
        model_path = VOICE_MODELS[language]
        if not model_path.is_file():
            raise FileNotFoundError(f"Voice model not found: {model_path}")
        _loaded_voices[language] = PiperVoice.load(str(model_path))
    return _loaded_voices[language]


def speak_text(text: str, language: str = "en") -> str:
    """Generate speech and return the absolute path to a valid WAV file."""
    text = (text or "").strip()
    if not text:
        raise ValueError("Cannot generate speech from empty text.")

    voice = _get_voice(language)
    output_path = OUTPUT_DIR / f"speech_{time.time_ns()}.wav"

    # synthesize_wav configures the WAV header and writes audio samples.
    with wave.open(str(output_path), "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)

    # Fail clearly if synthesis produced only an empty WAV header.
    with wave.open(str(output_path), "rb") as wav_file:
        if wav_file.getnframes() <= 0:
            output_path.unlink(missing_ok=True)
            raise RuntimeError("Piper generated a WAV file with no audio samples.")

    return str(output_path.resolve())
