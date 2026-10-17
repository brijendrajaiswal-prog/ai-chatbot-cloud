import subprocess
import wave
from pathlib import Path

BASE_DIR = Path(r"C:\AIChatbot")

PIPER = BASE_DIR / ".venv" / "Scripts" / "piper.exe"
MODEL = BASE_DIR / "voices" / "hi_IN-pratham-medium.onnx"
OUTPUT = BASE_DIR / "hindi_test.wav"
TEXT_FILE = BASE_DIR / "hindi_text.txt"

# Read the Hindi text from a UTF-8 file.
text = TEXT_FILE.read_text(encoding="utf-8").strip()

# Remove any previous invalid audio file.
if OUTPUT.exists():
    OUTPUT.unlink()

print("Generating Hindi audio...")

try:
    with subprocess.Popen(
        [
            str(PIPER),
            "--model",
            str(MODEL),
            "--output_file",
            str(OUTPUT),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    ) as process:

        _, stderr = process.communicate(
            input=text.encode("utf-8"),
            timeout=120,
        )

    print("Piper exit code:", process.returncode)

    if stderr:
        print("Piper messages:")
        print(stderr.decode("utf-8", errors="replace"))

    if process.returncode != 0:
        print("Audio generation failed.")
    elif not OUTPUT.exists():
        print("Audio file was not created.")
    else:
        print("File size:", OUTPUT.stat().st_size, "bytes")

        with wave.open(str(OUTPUT), "rb") as audio:
            duration = audio.getnframes() / audio.getframerate()
            print("Channels:", audio.getnchannels())
            print("Sample rate:", audio.getframerate())
            print("Duration:", round(duration, 2), "seconds")

        print("Hindi audio generated successfully!")

except Exception as error:
    print("Error:", repr(error))