from pathlib import Path
from piper import espeakbridge

BASE_DIR = Path(r"C:\AIChatbot")
DATA_DIR = (
    BASE_DIR
    / ".venv"
    / "Lib"
    / "site-packages"
    / "piper"
    / "espeak-ng-data"
)

print("eSpeak data exists:", DATA_DIR.exists())

try:
    espeakbridge.initialize(str(DATA_DIR))
    print("eSpeak initialization successful")

    espeakbridge.set_voice("hi")

    text = (BASE_DIR / "hindi_text.txt").read_text(
        encoding="utf-8"
    ).strip()

    print("Testing Hindi phonemization...")

    result = espeakbridge.get_phonemes(text)

    print("Phonemization successful!")
    print("Result:", result)

except Exception as error:
    print("Phonemization failed!")
    print("Error type:", type(error).__name__)
    print("Error:", repr(error))