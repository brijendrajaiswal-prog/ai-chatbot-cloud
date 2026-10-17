from faster_whisper import WhisperModel

# Lightweight multilingual speech recognition.
# Model files are downloaded automatically on first use.
_model = None


def get_model():
    global _model

    if _model is None:
        _model = WhisperModel(
            "small",
            device="cpu",
            compute_type="int8"
        )

    return _model


def transcribe_audio(audio_path):
    """
    Convert recorded Hindi or English speech into text.
    """

    model = get_model()

    segments, info = model.transcribe(
        audio_path,
        language=None,
        beam_size=1,
        vad_filter=True
    )

    text = " ".join(
        segment.text.strip()
        for segment in segments
    ).strip()

    return {
        "text": text,
        "language": info.language
    }