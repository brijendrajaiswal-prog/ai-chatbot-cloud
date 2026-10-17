import subprocess
import tempfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent

PIPER_EXE = PROJECT_DIR / ".venv" / "Scripts" / "piper.exe"

HINDI_VOICE = PROJECT_DIR / "voices" / "hi_IN-pratham-medium.onnx"

ENGLISH_VOICE = PROJECT_DIR / "voices" / "en_US-amy-medium.onnx"


def speak_text(text, language="en"):
    """Generate speech using a local Piper voice."""

    voice = HINDI_VOICE if language == "hi" else ENGLISH_VOICE

    if not PIPER_EXE.exists():
        raise FileNotFoundError(f"Piper not found: {PIPER_EXE}")

    if not voice.exists():
        raise FileNotFoundError(f"Voice model not found: {voice}")

    with tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False
    ) as audio_file:
        output_path = Path(audio_file.name)

    try:
        subprocess.run(
            [
                str(PIPER_EXE),
                "--model",
                str(voice),
                "--output_file",
                str(output_path),
            ],
            input=text,
            text=True,
            encoding="utf-8",
            check=True,
            capture_output=True,
            timeout=120,
        )

        return str(output_path)

    except Exception:
        output_path.unlink(missing_ok=True)
        raise