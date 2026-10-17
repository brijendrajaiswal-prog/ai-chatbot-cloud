import subprocess
from pathlib import Path

PROJECT = Path(r"C:\AIChatbot")

PIPER = PROJECT / ".venv" / "Scripts" / "piper.exe"

MODEL = PROJECT / "voices" / "hi_IN-pratham-medium.onnx"

OUTPUT = PROJECT / "hindi_test_fixed.wav"

# Write Hindi text using Python's Unicode support.
text = "\u0928\u092e\u0938\u094d\u0924\u0947\u0964"

print("Testing Hindi voice model...")

if not PIPER.exists():
    raise FileNotFoundError(f"Piper not found: {PIPER}")

if not MODEL.exists():
    raise FileNotFoundError(f"Hindi model not found: {MODEL}")

result = subprocess.run(
    [
        str(PIPER),
        "--model",
        str(MODEL),
        "--output_file",
        str(OUTPUT),
    ],
    input=text,
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    timeout=120,
)

if result.returncode != 0:
    print("Piper failed:")
    print(result.stderr)
    raise SystemExit(result.returncode)

if not OUTPUT.exists() or OUTPUT.stat().st_size == 0:
    raise RuntimeError("Piper did not generate a valid audio file.")

print("Audio generated successfully:", OUTPUT)
print("File size:", OUTPUT.stat().st_size, "bytes")