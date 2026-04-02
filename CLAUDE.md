# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

A personal voice cloning project that generates audio narration for a London walking tour using a father's voice. All processing runs fully locally — no audio or data leaves the machine.

## Running the Generator

```bash
# Activate the conda environment (configured in .vscode/settings.json)
python src/generate.py
```

First run downloads ~2GB of Chatterbox model weights automatically.

**Convert WAV output to MP3 for web use (PowerShell):**
```powershell
Get-ChildItem output\*.wav | ForEach-Object {
    ffmpeg -i $_.FullName -codec:audio libmp3lame -b:a 192k ($_.FullName -replace '\.wav$','.mp3')
}
```

**Or on bash/Linux:**
```bash
cd output
for f in *.wav; do ffmpeg -i "$f" -codec:audio libmp3lame -b:a 192k "${f%.wav}.mp3"; done
```

## Dependencies

Install manually (no requirements.txt):
```bash
pip install chatterbox-tts torch torchaudio
```

External: `ffmpeg` (for MP3 conversion). Check with `ffmpeg -version`.

Hardware: NVIDIA GPU with 4GB+ VRAM (6GB+ recommended). Verify with `nvidia-smi`.

Python 3.10 or 3.11 recommended (3.12+ can have ML library compatibility issues).

## Architecture

**`src/generate.py`** — the only script. It:
1. Detects GPU (CUDA) or falls back to CPU
2. Loads ChatterboxTTS model from pretrained weights
3. Iterates over a `stops` dict (`filename → narration_text`)
4. Calls `model.generate(text, audio_prompt_path=REFERENCE_AUDIO)` for each stop
5. Saves WAV tensors to `output/` via `torchaudio.save()`

**Reference audio:** `Recordings_original/Musashi_Jamie.m4a` is the active voice reference. Two alternatives exist in the same folder. A 5–30 second clip is sufficient for zero-shot cloning — no fine-tuning required.

**Web interface:** `london_tour.html` is a static HTML page with vintage styling (aged paper aesthetic) that embeds audio players for each tour stop. It expects MP3 files from the `output/` directory.

## Adding New Tour Stops

Add entries to the `stops` dict in `src/generate.py`:
```python
stops = {
    "01.introduction": "...",
    "02.gray_inn": "Text for stop 2...",
    "03.smithfield": "Text for stop 3...",
}
```

File naming convention: `NN.stop_name` (zero-padded number prefix).

## Quality Tuning

- Flat voice → record more reference audio with varied emotion and pacing
- Mispronounced words → break long sentences into shorter ones, or spell words phonetically
- Inconsistent quality → use the same reference audio clip for all stops

## Planned Iterations

- **v1.5:** Fine-tune XTTS v2 on more reference audio for higher fidelity
- **v2:** Progressive Web App with GPS-triggered playback (browser Geolocation API)
- **v2.5:** Map view with route and stop markers
- **v3:** Native mobile app (React Native + expo-location)
