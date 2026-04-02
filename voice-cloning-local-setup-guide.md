# Local Voice Cloning Setup Guide
## Dad's Walking Tour — Voice Narration Project

---

## What You're Building

A fully local voice cloning pipeline where your dad's voice data **never leaves your machine**. You'll record him, clone his voice using an open-source model, generate MP3 narration files for each tour stop, and embed them in a simple web page.

---

## Prerequisites

| Requirement | Details |
|---|---|
| **GPU** | NVIDIA with 4GB+ VRAM (6GB+ recommended). Run `nvidia-smi` in terminal to confirm it's detected. |
| **Python** | 3.10 or 3.11 recommended (3.12+ can have compatibility issues with ML libraries) |
| **Storage** | ~5GB free for model weights + your audio files |
| **OS** | Windows 10/11 or Linux |
| **ffmpeg** | Required for audio processing (install instructions below) |

---

## Step 1: Set Up Your Python Environment

Open a terminal (PowerShell on Windows) and create an isolated environment so nothing conflicts with your system Python.

```bash
# Create a project folder
mkdir voice-tour
cd voice-tour

# Create a virtual environment
python -m venv .venv

# Activate it
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# You should see (.venv) at the start of your prompt now
```

### Install ffmpeg

ffmpeg handles audio format conversion. Check if you already have it:

```bash
ffmpeg -version
```

If not installed:

- **Windows (winget):** `winget install ffmpeg`
- **Windows (manual):** Download from https://ffmpeg.org/download.html, extract, add the `bin` folder to your PATH
- **Linux:** `sudo apt install ffmpeg`

---

## Step 2: Choose Your Model

You have two strong local options. **Start with Chatterbox** — it's the easiest to get running and produces great results.

### Option A: Chatterbox (Recommended First Try)

- **License:** MIT (fully open, no restrictions)
- **Quality:** Outperforms many commercial tools in blind tests
- **Audio needed:** A few seconds of reference audio (no fine-tuning required)
- **Install:**

```bash
pip install chatterbox-tts
```

### Option B: Coqui XTTS v2 (Backup / More Control)

- **License:** Coqui Public Model License (non-commercial use only — fine for personal projects)
- **Quality:** Very good, well-documented, large community
- **Audio needed:** 6+ seconds minimum, better with more
- **Install:**

```bash
pip install coqui-tts
```

> **Note:** The first time you run either model, it will download weights (~2GB). This only happens once.

---

## Step 3: Record Your Dad

This is the most important step. Better recordings = better voice clone.

### Equipment (in order of preference)

1. **USB microphone** into a laptop (e.g., Blue Yeti, Audio-Technica ATR2100x — ~$50-$100)
2. **Phone voice memo app** — surprisingly good if you follow the environment tips below
3. **Wired earbuds with a mic** — better than laptop mic, worse than USB mic

### Recording Environment

- **Quiet room** — turn off fans, AC, close windows
- **Soft surfaces** — a bedroom or closet with clothes absorbs echo. Avoid kitchens/bathrooms (hard surfaces)
- **Consistent distance** — keep the mic 6-12 inches from his mouth
- **No handling noise** — set the phone/mic on a stable surface

### What to Record

| Recording | Purpose | Length |
|---|---|---|
| **Tour script** (each stop as a separate file) | These become your final narration source text | Varies |
| **Extra reading material** (a news article, book passage, etc.) | Gives the model more vocal range to learn from | 5-10 min |
| **Casual talking** (tell a story, describe the neighbourhood) | Captures natural cadence and personality | 5-10 min |

### Recording Tips

- Use **WAV format** if possible (higher quality than MP3 for training). Most voice memo apps default to this.
- Record in **short segments** (2-3 minutes each) so you can discard bad takes
- Have him speak naturally — not "announcer voice"
- If he stumbles, just pause and re-say the sentence. You can trim later.
- **Label files clearly:** `stop01_main_street.wav`, `extra_reading_01.wav`, etc.

### Audio Cleanup (Optional but Helpful)

If there's background noise, you can clean it up with Audacity (free):

1. Download from https://www.audacityteam.org/
2. Open recording → select a quiet section (just noise, no speech) → Effect → Noise Reduction → Get Noise Profile
3. Select all → Effect → Noise Reduction → OK
4. Export as WAV

---

## Step 4: Clone the Voice & Generate Audio

### Option A: Using Chatterbox

Create a file called `generate.py` in your `voice-tour` folder:

```python
import torch
from chatterbox.tts import ChatterboxTTS

# Load model (downloads weights on first run)
device = "cuda" if torch.cuda.is_available() else "cpu"
model = ChatterboxTTS.from_pretrained(device=device)

# Path to your dad's reference audio (WAV or MP3, 5-30 seconds works best)
REFERENCE_AUDIO = "recordings/dad_sample.wav"

# Tour stops — add your actual script text here
stops = {
    "stop01_main_street": "Welcome to Main Street. This road was first paved in 1923...",
    "stop02_old_church": "If you look to your left, you'll see the old Methodist church...",
    "stop03_town_square": "We're now standing in the town square...",
}

# Generate audio for each stop
for filename, text in stops.items():
    print(f"Generating: {filename}...")
    wav_tensor = model.generate(text, audio_prompt_path=REFERENCE_AUDIO)

    # Save as WAV
    import torchaudio
    torchaudio.save(f"output/{filename}.wav", wav_tensor, model.sr)

print("Done! Check the output/ folder.")
```

Before running, create the output folder:

```bash
mkdir output
mkdir recordings
# Copy your dad's audio files into the recordings/ folder
```

Run it:

```bash
python generate.py
```

### Option B: Using Coqui XTTS v2

Create a file called `generate.py` in your `voice-tour` folder:

```python
import torch
from TTS.api import TTS

# Detect GPU
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load XTTS v2 (downloads weights on first run)
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

# Path to your dad's reference audio
# You can pass multiple files for better quality
REFERENCE_AUDIO = ["recordings/dad_sample_01.wav", "recordings/dad_sample_02.wav"]

# Tour stops
stops = {
    "stop01_main_street": "Welcome to Main Street. This road was first paved in 1923...",
    "stop02_old_church": "If you look to your left, you'll see the old Methodist church...",
    "stop03_town_square": "We're now standing in the town square...",
}

# Generate audio for each stop
for filename, text in stops.items():
    print(f"Generating: {filename}...")
    tts.tts_to_file(
        text=text,
        file_path=f"output/{filename}.wav",
        speaker_wav=REFERENCE_AUDIO,
        language="en"
    )

print("Done! Check the output/ folder.")
```

Run the same way:

```bash
mkdir output
mkdir recordings
python generate.py
```

---

## Step 5: Convert to MP3 (for Web Use)

WAV files are large. Convert to MP3 for your web page:

```bash
# Convert all WAV files in output/ to MP3
cd output
for f in *.wav; do ffmpeg -i "$f" -codec:audio libmp3lame -b:a 192k "${f%.wav}.mp3"; done
```

On **Windows PowerShell:**

```powershell
Get-ChildItem output\*.wav | ForEach-Object {
    ffmpeg -i $_.FullName -codec:audio libmp3lame -b:a 192k ($_.FullName -replace '\.wav$','.mp3')
}
```

---

## Step 6: Listen & Iterate

This is where you tune the quality:

- **If the voice sounds flat:** Record more reference audio with varied emotion and pacing
- **If words are mispronounced:** Break long sentences into shorter ones, or spell out unusual words phonetically in the script
- **If quality varies between stops:** Use the same reference audio clip(s) for all stops for consistency
- **XTTS v2 specific:** You can fine-tune the model on your dad's voice for significantly better results (more advanced — good candidate for a later iteration)

---

## Folder Structure When You're Done

```
voice-tour/
├── .venv/                  # Python virtual environment
├── recordings/             # Your dad's raw audio files (KEEP THESE SAFE)
│   ├── dad_sample_01.wav
│   ├── dad_sample_02.wav
│   └── ...
├── output/                 # Generated narration
│   ├── stop01_main_street.wav
│   ├── stop01_main_street.mp3
│   └── ...
├── generate.py             # Your generation script
└── tour-script.txt         # The written tour (for reference)
```

---

## Privacy Checklist

- [x] Model runs 100% locally on your GPU
- [x] No audio uploaded to any cloud service
- [x] No API keys or accounts required
- [x] Your dad's voice data stays in `recordings/` on your machine
- [x] You can delete everything by removing the `voice-tour/` folder
- [ ] **Backup `recordings/` to an encrypted external drive** — these are irreplaceable

---

## What's Next (Future Iterations)

| Iteration | Description |
|---|---|
| **v1** | Simple HTML page with play buttons per stop (next step — bring your MP3s back here and I can help build this) |
| **v1.5** | Fine-tune XTTS v2 on more of your dad's audio for higher fidelity |
| **v2** | Progressive Web App (PWA) with GPS-triggered playback using the browser Geolocation API |
| **v2.5** | Add a map view showing the route with stop markers |
| **v3** | Native mobile app with offline support via React Native + expo-location |
