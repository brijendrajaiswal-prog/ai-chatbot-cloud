from pathlib import Path
import subprocess

BASE = Path(r"C:\AIChatbot")
PIPER = BASE / ".venv" / "Scripts" / "piper.exe"

tests = [
    ("English", "Hello, how are you?", "en_US-amy-medium.onnx"),
    ("Hindi", "नमस्ते", "hi_IN-pratham-medium.onnx"),
]

for language, text, model_name in tests:
    print(f"\nTesting {language}...")

    output = BASE / f"{language.lower()}_phonemizer_test.wav"
    model = BASE / "voices" / model_name

    if output.exists():
        output.unlink()

    result = subprocess.run(
        [
            str(PIPER),
            "--model", str(model),
            "--output_file", str(output),
        ],
        input=text.encode("utf-8"),
        capture_output=True,
        timeout=120,
    )

    print("Exit code:", result.returncode)
    print("WAV created:", output.exists())
    print(
        result.stderr.decode("utf-8", errors="replace")[-1500:]
    )