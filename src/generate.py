import os
import subprocess
import numpy as np
import torch
import torchaudio
from chatterbox.tts import ChatterboxTTS


def load_audio_ffmpeg(path: str, target_sr: int) -> torch.Tensor:
    """Load any audio format (including M4A) via ffmpeg, returning a mono tensor at target_sr."""
    cmd = [
        "ffmpeg", "-y", "-i", path,
        "-f", "f32le", "-acodec", "pcm_f32le",
        "-ar", str(target_sr), "-ac", "1",
        "-"
    ]
    result = subprocess.run(cmd, capture_output=True)
    wav = torch.from_numpy(np.frombuffer(result.stdout, dtype=np.float32)).unsqueeze(0)
    return wav

REFERENCE_FILES = [
    # "Recordings_original/Musashi_Jamie.m4a",
    # "Recordings_original/20000 Leagues_Jamie.m4a",
    # "Recordings_original/WutherHeights_Jamie.m4a",
    "Recordings_original/Runner_path_Jamie.m4a",
  
]
BLENDED_REFERENCE = "Recordings_original/reference_blended.wav"
TRIM_SECONDS = 60   # seconds to take from each recording
PAUSE_MS = 300      # silence between sentence chunks (milliseconds)


def build_blended_reference(target_sr: int):
    if os.path.exists(BLENDED_REFERENCE):
        print("Using existing blended reference.")
        return
    clips = []
    for path in REFERENCE_FILES:
        wav = load_audio_ffmpeg(path, target_sr)
        wav = wav[:, : target_sr * TRIM_SECONDS]     # trim
        clips.append(wav)
    blended = torch.cat(clips, dim=1)
    torchaudio.save(BLENDED_REFERENCE, blended, target_sr)
    print(f"Blended reference saved: {BLENDED_REFERENCE}")


def chunk_by_sentence(text: str) -> list:
    sentences = text.split(".")
    return [s.strip() + "." for s in sentences if s.strip()]


def generate_stop(text: str) -> torch.Tensor:
    pause = torch.zeros(1, int(model.sr * PAUSE_MS / 1000))
    parts = []
    chunks = chunk_by_sentence(text)
    for i, chunk in enumerate(chunks):
        print(f"  chunk {i + 1}/{len(chunks)}: {chunk[:60]}...")
        wav = model.generate(chunk, audio_prompt_path=REFERENCE_AUDIO, exaggeration =0.75)
        parts.append(wav)
        if i < len(chunks) - 1:
            parts.append(pause)
    return torch.cat(parts, dim=1)


# Load model (downloads weights on first run)
device = "cuda" if torch.cuda.is_available() else "cpu"
model = ChatterboxTTS.from_pretrained(device=device)

build_blended_reference(model.sr)
REFERENCE_AUDIO = BLENDED_REFERENCE

# Tour stops — add your actual script text here
stops = {
    "01.introduction": "This is not an ordinary London walking tour. It is a journey back through the streets of a young man's life — the pavements he walked each morning as a medical student, the pubs where he unwound, the market he picked his way through, and the hospital square where he fell rather helplessly in love.The route begins at Tavistock Square in Bloomsbury, where a nineteen-year-old arrived in September 1964 with a place at St Bartholomew's Hospital Medical College — Barts, to those who know it — and rather more ambition than experience. It ends at the hospital itself, on the far side of Smithfield, where that same young man graduated five years later as a doctor.Along the way you will pass the lawyers of Gray's Inn, the blood-stained cobbles of Smithfield Market (considerably cleaner these days), a Victorian pub of no particular distinction and therefore every distinction, one of the oldest churches in London, and a hospital square where nurses once wheeled patients out into the sunshine and a tall girl was easy to spot in a crowd.The walk is approximately two miles and quite level. Allow two to three hours if you stop at the recommended places — and do stop at the recommended places",
    "02-StudentHostel": "Your tour begins here, on the east side of Tavistock Square — a handsome Bloomsbury garden square that was rather more significant than it might appear to a fresh-faced eighteen-year-old arriving from school in September 1964. This was the student hostel for London University, and it was home for the first two years of medical training at Barts.Having arrived from the shared dormitories of school, this was the first experience of something approaching independent life — a room in a hostel, rather than home. Entertainment in the evenings was limited but reliable: studying, which was unfortunately rather necessary, and the television set in the common room, which drew a faithful crowd each night.For more adventurous evenings there were curry houses a block or two away — an education in itself for a young man in the 1960s, and far better value than the college canteen. The neighbourhood was and remains deeply academic: the British Medical Association, the Wellcome Collection, and University College London are all within easy walking distance.",
    "03.Grays Inn": "Not far into the walk, heading east along Holborn, you pass the entrance to Gray's Inn — one of the four Inns of Court that have trained English barristers since the fourteenth century. It is a rather fine set of gardens and buildings tucked behind the street, well worth a glance through the gates. This is not a pub, despite what the signage might suggest to the unwary visitor.Along this stretch there were once several curry houses that served the local medical and legal fraternity with admirable economy. In the 1960s a good curry could be had for very little, and on a student's grant that was no small consideration. The restaurants have changed over the decades, but the tradition of feeding hungry professionals cheaply and well in this part of London has never quite disappeared.Continuing east you turn off Holborn onto Charterhouse Street, beginning the descent toward Smithfield. The character of the streets changes here almost immediately — from the administrative grandeur of Holborn to something older, rougher, and considerably more interesting."
    #"04.Smithfield_FoxandAnchor": "By the time you reach Charterhouse Street you are in Smithfield territory, and in the 1960s that meant something quite specific: a street running red. Smithfield is London's great wholesale meat market, operating on this site in various forms since the twelfth century, and in those days the morning walk to college required a certain nimbleness of foot. The street was full of butchers in bloodied aprons, and the cobbles were not entirely free of the evidence of their trade.Rosie — who was training as a nurse at Barts and walking this same route — recalls that nurses in uniform were catcalled regularly. Men felt entitled to do that in those days, and nobody thought much of it. The nurses, however, were pragmatic: in exchange for tolerating the attention, they were rather generously supplied with free cuts of meat by butchers who held the nursing profession in genuine respect. A fair transaction, perhaps, by the standards of the time.The Fox and Anchor stands here at the edge of the market — a proper Victorian pub with dark wood, etched glass, and the particular atmosphere of a place that has been serving early-morning pints to market workers since before memory. It was a regular haunt, separate from the bar in the college itself, and it retains its character to this day. The Malmaison Hotel next door occupies what was formerly the nurses' accommodation block. Many hours were spent waiting in its foyer. Boris, the porter, saw to it that no one got any further.Stop here for a beer. The Fox and Anchor still opens at 7 a.m. to serve the market workers — one of the few London pubs with a breakfast licence. It is exactly as good as it sounds.",
    #"05.ChatterhouseSquare":"Charterhouse Square is one of those London squares that rewards the visitor who pauses long enough to look properly. The buildings around it span several centuries, and at its heart stands Charterhouse itself — a medieval monastery turned Tudor mansion turned charitable institution, with a history that reads like a condensed account of English civilisation from 1371 onwards. It is well worth exploring on its own merits.For the medical student of 1966, however, Charterhouse Square meant something more immediate: the college. This was home, workplace, and social centre for three years. The anatomy department was to the right as you walked in — a place of long, concentrated hours and the particular smell of formaldehyde that no amount of subsequent experience entirely removes from the memory. Biochemistry occupied the north end of the central grass. The library was to the north-west, a place of refuge and occasional panic in equal measure. The residence was to the north-east, and contained — crucially — a bar. The combination of living accommodation, lecture rooms, dissection theatres, and licensed premises in a single address produced, predictably, a social atmosphere of considerable intensity. Wild parties and long nights of studying coexisted in close proximity, as they do wherever young people are working hard and living together, and the balance between the two shifted depending on the proximity of examinations.Note: to access the college from the street, you needed to come to the corner of Charterhouse Square — the entrance is not immediately obvious from Charterhouse Street itself.Try to gain access to the square and courtyard — it is sometimes possible during opening hours. The Charterhouse building on the south side runs regular guided tours and is a remarkable piece of London history entirely separate from the medical college.",
    #"06.HandandShears":"Leaving the college, go down the side of Charterhouse Square, turn into Hayne Street, and carry straight across Long Lane. You are now in the ancient lanes around Cloth Fair, one of the oldest surviving streets in the City of London — the great fire of 1666 stopped just short of here, which is why the buildings have a different character from the wider City.At the end of this short walk you come to the Hand and Shears. It is, in the best possible sense, nothing special. No historic grandeur, no famous associations, no particular claim on the tourist's attention. It is a Victorian pub of the ordinary sort — dark, comfortable, slightly worn, and entirely itself. Which is, of course, precisely what makes it special. London has been losing pubs like this for decades, and each one that disappears takes a piece of the city's character with it.This was the regular pub — the one used on ordinary evenings when the bar in the college felt too close to home, or when a change of air was wanted. It is not a destination in the way that some pubs are destinations. It is a local, in the proper sense of that word, and the Hand and Shears has been serving the neighbourhood in much the same fashion since the sixteenth century, when it provided refreshment for the cloth merchants of the fair that gave the nearby street its name.",
    #"07.StBartholomewsTheGreat":"Continuing along Cloth Fair, you come out onto West Smithfield and very shortly arrive at the entrance to St Bartholomew-the-Great — a church that has been standing here, in one form or another, since 1123. That is not a misprint. Nine centuries of Londoners have worshipped, married, baptised their children, and buried their dead in this building, and the weight of that continuity is palpable the moment you step inside.Do go in. The interior is Norman — massive round arches, thick piers, a chancel that feels ancient in the way that very few English buildings still manage to feel ancient. It has survived the Dissolution, the Great Fire, the Blitz, and several centuries of general neglect with its essential character intact. It was used as a stable and a printer's workshop at various points in its history, which gives it a certain robustness.Do not be alarmed by the statue of St Bartholomew holding a complete human skin. The apostle was martyred by flaying, which is why he is the patron saint of tanners, leather workers, and — perhaps not coincidentally — the hospital that bears his name. It is a striking piece of iconography by the standards of the Church of England, which usually inclines toward the restrained. It is also, it must be said, a little gross. But one becomes accustomed to such things when studying medicine",
    #"08.StBartholomewsHospital":"Through the Henry VIII gatehouse — the only remaining Tudor gateway in London, which gives you some sense of the age of this institution — and into the hospital square. Barts was founded in 1123, the same year as the church next door, making it the oldest hospital in Britain still operating on its original site. It has been healing the sick of London for nine hundred years, and the square at its centre has seen a great deal of history.In the 1960s, on fine days, nurses would wheel patients' beds out into the square for fresh air and sunshine. It was a sight that belongs entirely to its era — the cheerful practicality of it, the assumption that outdoor air was good medicine in itself, the beds arranged in the afternoon light with patients blinking at the sky. It would not happen today, for a variety of sensible and slightly sad reasons.For a medical student it was also useful, in that a tall nurse was easy to spot at some distance across a sunlit square. Rosie was the tallest of her nursing cohort, which made identification considerably simpler than it might otherwise have been.As a student, all the buildings around the square were visited in the course of training — medicine, surgery, obstetrics, psychiatry, the lot. After graduation, I was the house doctor in the orthopaedic ward, on the right-hand side as you pass through to the square. On the left, through the arch, there is a building that has been under construction for some years — it contains the Great Hall, and on the staircase inside hangs a vast painting by William Hogarth, commissioned in 1734. In 2019 the Class of 1969 held their fiftieth anniversary reunion there. It had not changed as much as the people had.",
    #"09.StBartholomewsHospitalMuseum":"Within the hospital complex, clearly signposted once you are inside the gates, is the St Bartholomew's Hospital Museum — a small but exceptionally good museum devoted to the nine-hundred-year history of this institution. If you have any interest at all in the history of medicine, or in London history more broadly, a visit is strongly recommended.The collections cover the full span of the hospital's existence: surgical instruments, medical records, nursing uniforms, historical documents, and artefacts from every era of the hospital's life. There are exhibits covering the hospital's role in both world wars, its place in the development of modern nursing, and the long succession of medical advances achieved within its walls.It also contains, should you be visiting with a personal connection to the place, the particular pleasure of finding evidence that the institution you knew as a student has been quietly getting on with the business of healing people for considerably longer than any of its current staff or students have been alive. That is either humbling or reassuring, depending on your disposition. It is, on reflection, probably both.",
    #"10.StPauls":"South and slightly east of the hospital, a ten-minute walk through the lanes, stands St Paul's Cathedral — Wren's masterpiece, completed in 1711 after the Great Fire destroyed its predecessor, and still one of the most magnificent buildings in Europe.On the 30th of January, 1965, a young medical student stood in the street outside this cathedral with thousands of other Londoners and watched Winston Churchill's coffin carried past on a gun carriage. Churchill had died nine days earlier, at the age of ninety, and the state funeral was the largest in British history. The streets were lined from Westminster all the way to St Paul's, and the crowd stood in near silence.He had been eighteen years old, arriving in London less than five months earlier. He had not yet been alive during the war that Churchill had led, but he had grown up entirely within its shadow — in the stories of parents and teachers and neighbours, in the bomb damage still visible in cities, in the particular seriousness with which his generation understood what had been at stake. Standing in that crowd, on that cold January day, was one of those moments that makes itself permanent in the memory without any effort at all.St Paul's is worth visiting in its own right, of course — the crypt, the Whispering Gallery, the dome, the memorials. But it is also worth standing outside for a moment, as a medical student once did, and simply understanding where you are standing.",
    #"11.Conclusion":"This has been a short tour of a life lived between 1964 and 1969, across the streets of central London, in the process of becoming a doctor. It was, in almost every respect, an excellent five years — full of work and friendship and curry and the particular intensity of living in close quarters with a group of people all attempting, with varying degrees of success, the same difficult thing at the same time.The streets have changed considerably. Smithfield is clean now, which is an improvement. The nurses' accommodation is a hotel. The curry houses have moved on. The college itself has been absorbed into larger institutional structures that would have meant nothing to a student in 1964. And yet the buildings remain, and the square remains, and the fountain remains, and the Hogarth paintings are still on the wall of the staircase where they have always been.It is a slightly surprising thing to find oneself sharing this tour in written form rather than in person, as one would have preferred. But life arranges itself as it will, and there is something to be said for a walk that can be taken at any time, in any weather, by anyone who is curious about what this part of London looked like through the eyes of an eighteen-year-old arriving from somewhere else, with everything still ahead of him.What is perhaps most surprising is this: in a few weeks' time, eight of those eighteen-year-olds from 1964 will gather together again. All of them approaching eighty. All of them having lived very different lives, in very different places, following very different paths from the same starting point on Tavistock Square. Medicine, it turns out, is excellent preparation for a great many things — not least the company of old friends."
    }

# Generate audio for each stop
for filename, text in stops.items():
    print(f"Generating: {filename}...")
    wav_tensor = generate_stop(text)
    torchaudio.save(f"output/{filename}.wav", wav_tensor, model.sr)

print("Done! Check the output/ folder.")
