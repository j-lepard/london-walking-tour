# A London Walk — Voice-Cloned Audio Walking Tour

A personal project that generates narrated audio for a self-guided London walking tour using zero-shot voice cloning. The narrator's voice is cloned locally from a short reference recording; all processing stays on-device. The finished tour is served as a static web page hosted on GitHub Pages, with GPS-triggered audio playback when the user is within 50 metres of each stop.

The tour covers the streets of Bloomsbury and Smithfield walked by a medical student between 1964 and 1969 — from the student hostel at Tavistock Square to St Bartholomew's Hospital, where he graduated as a doctor.

---

## Architecture overview

```
src/generate.py          # Offline: voice-clone the narration to WAV, convert to MP3
index.html               # Online: static tour UI with GPS-triggered playback
output/                  # Generated MP3s (git-ignored; must be produced locally)
Recordings_original/     # Source voice reference recordings (git-ignored)
```

### Audio generation pipeline (`src/generate.py`)

1. Loads a reference M4A recording via `ffmpeg` and builds a blended reference clip
2. Loads [ChatterboxTTS](https://github.com/resemble-ai/chatterbox) (zero-shot TTS, ~2 GB weights downloaded on first run)
3. Splits each stop's narration text at sentence boundaries (`.`)
4. Generates a WAV tensor per sentence with `model.generate(chunk, audio_prompt_path=...)`
5. Concatenates sentence audio with 300 ms silence gaps between sentences
6. Saves full-stop WAVs to `output/`; user converts to MP3 with `ffmpeg`

### Web front-end (`index.html`)

- Vintage "aged paper" aesthetic — Playfair Display / IM Fell English / Special Elite fonts, grain overlay, London-red nav
- Sticky nav bar with a **▶ Start Tour** GPS button as the first item, followed by anchor links to each stop; horizontally scrollable on mobile
- GPS playback engine: `navigator.geolocation.watchPosition` polls position every 1–3 s (Android) or 5–10 s (iOS Safari)
- Haversine formula calculates distance to each stop; audio plays automatically when the user is within 50 m
- Each stop plays at most once per session (tracked with a `Set`)
- Hosted on GitHub Pages (HTTPS required for the Geolocation API)

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.10 or 3.11 | 3.12+ can have ML library compatibility issues |
| NVIDIA GPU, 4 GB+ VRAM | 6 GB+ recommended; CPU fallback is very slow |
| CUDA drivers | Verify with `nvidia-smi` |
| `ffmpeg` on PATH | For loading M4A reference audio and MP3 conversion |
| `pip install chatterbox-tts torch torchaudio` | No `requirements.txt`; install manually |

---

## Quickstart

### 1. Clone and install

```bash
git clone https://github.com/j-lepard/london-walking-tour.git
cd london-walking-tour
pip install chatterbox-tts torch torchaudio
```

### 2. Add a voice reference recording

Place a 30–60 second M4A (or WAV) recording of the target voice in `Recordings_original/`. Update `REFERENCE_FILES` in `src/generate.py`:

```python
REFERENCE_FILES = [
    "Recordings_original/your_recording.m4a",
]
```

A single good recording is sufficient. Longer or more varied recordings improve fidelity.

### 3. Enable the tour stops you want to generate

In `src/generate.py`, the `stops` dict contains all narration text. Stops are commented out by default. Uncomment the ones you want:

```python
stops = {
    "02-StudentHostel": "Your tour begins here...",
    # "03.Grays Inn": "...",   ← uncomment to generate
}
```

### 4. Generate audio

```bash
python src/generate.py
```

On first run this downloads ~2 GB of model weights. Subsequent runs are fast. WAV files appear in `output/`.

### 5. Convert WAV to MP3

**Bash / macOS / Linux:**
```bash
cd output
for f in *.wav; do ffmpeg -i "$f" -codec:audio libmp3lame -b:a 192k "${f%.wav}.mp3"; done
```

**PowerShell (Windows):**
```powershell
Get-ChildItem output\*.wav | ForEach-Object {
    ffmpeg -i $_.FullName -codec:audio libmp3lame -b:a 192k ($_.FullName -replace '\.wav$','.mp3')
}
```

### 6. Deploy to GitHub Pages

```bash
git add output/*.mp3
git commit -m "Add generated audio for stops X, Y, Z"
git push origin master
```

Enable GitHub Pages on `master` branch in the repo Settings → Pages. The site is live at `https://<username>.github.io/<repo>/`.

---

## Tour stops

| # | Name | Coordinates |
|---|---|---|
| 0 | Introduction | User's current location |
| 1 | Tavistock Square | 51.5250, -0.1291 |
| 2 | Gray's Inn | 51.5185, -0.1077 |
| 3 | Fox & Anchor (Smithfield) | 51.5195, -0.1005 |
| 4 | Charterhouse Square | 51.5192, -0.0997 |
| 5 | Hand & Shears | 51.5189, -0.1001 |
| 6 | St Bartholomew-the-Great | 51.5189, -0.0997 |
| 7 | Barts Hospital | 51.5171, -0.1001 |
| 8 | Barts Museum | 51.5171, -0.1001 |
| 9 | St Paul's Cathedral | 51.5139, -0.0984 |

Trigger radius: 50 metres. Coordinates and radius are defined in the `STOPS` array in `index.html`.

---

## Configuration reference (`src/generate.py`)

| Variable | Default | Effect |
|---|---|---|
| `REFERENCE_FILES` | `[Runner_path_Jamie.m4a]` | Source audio for voice cloning |
| `TRIM_SECONDS` | `60` | Seconds to take from each reference file |
| `PAUSE_MS` | `300` | Silence gap between sentence chunks (ms) |
| `exaggeration` | `0.75` | Emotion/prosody intensity (0 = flat, 1 = expressive) |

### Quality tuning tips

- **Flat or monotone voice** — record more reference audio with varied emotion and pacing; use a longer `TRIM_SECONDS`
- **Mispronounced words** — break long sentences shorter in the `stops` dict, or spell words phonetically
- **American accent bleeding through** — use a reference recording with slow, clearly British speech; increase `TRIM_SECONDS`
- **Inconsistent quality between stops** — always use the same `BLENDED_REFERENCE` path for all stops (the default behaviour)

---

## Repository structure

```
.
├── src/
│   └── generate.py          # TTS generation script
├── index.html               # Static tour web app
├── output/                  # Generated audio (git-ignored *.wav; MP3s committed)
├── Recordings_original/     # Voice reference audio (git-ignored)
├── recording_versions/      # Archived experiment outputs (git-ignored)
├── .gitignore
├── CLAUDE.md                # AI assistant instructions
├── Version notes.md         # Experiment log
└── README.md
```

---

## Roadmap

| Version | Description |
|---|---|
| v1 (current) | Zero-shot voice cloning; GPS-triggered static web player |
| v1.5 | Fine-tune XTTS v2 on more reference audio for higher fidelity |
| v2 | Progressive Web App — compass bearing and distance guidance to next stop |
| v2.5 | Map view with route polyline and stop markers |
| v3 | Native mobile app (React Native + expo-location) |

---

## Privacy

All voice cloning runs locally — no audio, text, or personal data leaves the machine during generation. The finished MP3 files are served as static assets from GitHub Pages.

---

## License

Personal / private use. The narration text and voice recordings are the intellectual property of the original narrator.
