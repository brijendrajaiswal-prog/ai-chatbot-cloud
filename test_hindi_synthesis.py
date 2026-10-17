from pathlib import Path
import wave

from piper import PiperVoice

BASE_DIR = Path(r"C:\AIChatbot")
MODEL = BASE_DIR / "voices" / "hi_IN-pratham-medium.onnx"
OUTPUT = BASE_DIR / "hindi_python_test.wav"

print("Loading Hindi model...")

voice = PiperVoice.load(str(MODEL))
print("Hindi model loaded.")

text = "नमस्ते। आपका स्वागत है।"

with wave.open(str(OUTPUT), "wb") as wav_file:
    # Piper's synthesize_wav method configures the WAV
    # header and writes the generated audio samples.
    voice.synthesize_wav(text, wav_file)

print("File size:", OUTPUT.stat().st_size, "bytes")

with wave.open(str(OUTPUT), "rb") as wav_file:
    frames = wav_file.getnframes()
    rate = wav_file.getframerate()
    duration = frames / rate

    print("Channels:", wav_file.getnchannels())
    print("Sample rate:", rate)
    print("Frames:", frames)
    print("Duration:", round(duration, 2), "seconds")

if duration > 0:
    print("SUCCESS: Audio samples were generated.")
else:
    print("ERROR: The WAV file contains no audio samples.")