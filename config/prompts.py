"""
BGM and Music Prompts Configuration
Author: Sarath

Contains all music generation prompts organized by emotion and segment.
"""

# Emotion to music prompt mapping - melodious and harmonious prompts
EMOTION_MUSIC_MAP = {
    "wonder": {
        "prompt": "soft piano melody with gentle ambient pads, smooth ethereal soundscape, melodic and harmonious, dreamy major key, flowing arpeggios, peaceful cinematic background",
        "duration": 30
    },
    "curiosity": {
        "prompt": "gentle melodic piano with soft synthesizer pads, playful and smooth, light harmonious textures, medium tempo, warm ambient background music",
        "duration": 30
    },
    "tension": {
        "prompt": "subtle dramatic strings with melodic progression, building anticipation, smooth orchestral layers, gentle crescendo, harmonious minor key, cinematic and elegant",
        "duration": 30
    },
    "triumph": {
        "prompt": "uplifting orchestral melody with inspiring piano, harmonious brass ensemble, soaring strings, triumphant and melodic, major key, smooth cinematic score",
        "duration": 30
    },
    "melancholy": {
        "prompt": "gentle melancholic piano melody, soft flowing strings, smooth and melodic, reflective harmonious ambient, slow tempo, warm emotional soundscape",
        "duration": 30
    },
    "intrigue": {
        "prompt": "smooth mysterious piano melody, gentle ambient textures, harmonious and melodic, subtle elegant progression, warm documentary style background",
        "duration": 30
    },
    "excitement": {
        "prompt": "upbeat melodic piano with smooth synthesizers, harmonious and joyful, gentle energy, major key, pleasant rhythmic background music",
        "duration": 30
    },
    "reflection": {
        "prompt": "calm melodic piano with gentle ambient pads, smooth peaceful soundscape, harmonious and meditative, soft flowing melodies, warm background",
        "duration": 30
    },
    "restlessness": {
        "prompt": "gentle building melody with soft rhythmic pulse, smooth anticipation, melodic progression, harmonious layered textures, warm ambient energy",
        "duration": 30
    },
    "explosive energy": {
        "prompt": "energetic melodic rock with harmonious guitar, smooth driving rhythm, uplifting crescendo, major key, pleasant powerful music",
        "duration": 30
    },
    "rebellion": {
        "prompt": "energetic but melodic rock music, driving rhythm with harmonious guitar riffs, smooth powerful progression, uplifting energy, pleasant rock soundscape",
        "duration": 30
    },
    "liberation": {
        "prompt": "soaring melodic strings with uplifting piano, triumphant harmony, smooth flowing melody, major key, gentle euphoric soundscape, harmonious freedom music",
        "duration": 30
    },
    "experimentation": {
        "prompt": "creative melodic textures with smooth ambient pads, harmonious innovative sounds, gentle electronic elements, pleasant artistic soundscape",
        "duration": 30
    },
    "mastery": {
        "prompt": "elegant piano melody with sophisticated strings, confident and smooth, harmonious arrangement, refined cinematic sound, gentle triumphant resolution",
        "duration": 30
    },
    "intensity": {
        "prompt": "building orchestral melody with smooth strings, harmonious dramatic progression, elegant crescendo, melodic and refined, cinematic tension",
        "duration": 30
    }
}

DEFAULT_MUSIC = {
    "prompt": "soft melodic ambient background music, gentle piano with smooth pads, harmonious and pleasant, warm cinematic soundscape",
    "duration": 30
}

# 9-Segment Daisy-Chain BGM Prompts
BGM_SEGMENT_PROMPTS = {
    1: {
        "name": "The Hook",
        "prompt": "Cinematic ambient soundscape, Iceland atmosphere, glacial wind textures, distant geothermal rumbling, minimal glass chimes, sense of mystery, cold but magical, high fidelity, 70 BPM, reverb-heavy flute in distance.",
        "duration": 45,
        "phase": "Origins"
    },
    2: {
        "name": "The Bohemian Commune",
        "prompt": "Warm acoustic folk fusion, gentle flute and acoustic guitar strumming, experimental textures blending with organic sounds, curious and whimsical, soft rhythmic pulse, creative and bohemian, 85 BPM, major key, sense of childhood wonder.",
        "duration": 128,
        "phase": "Origins"
    },
    3: {
        "name": "The Pre-Build",
        "prompt": "Building orchestral pop, piano arpeggios starting gently, confident rhythm emerging, hopeful and bright, feeling of anticipation, crisp production, 95 BPM.",
        "duration": 22,
        "phase": "Breakthrough"
    },
    4: {
        "name": "Inflection 1: The Triumph",
        "prompt": "Triumphant orchestral swell, sweeping strings section, bright synthesizer pads, major key, euphoric release, victory moment, rich and full sound, uplifting, 100 BPM.",
        "duration": 30,
        "phase": "Breakthrough"
    },
    5: {
        "name": "The Aftermath",
        "prompt": "Orchestral pop settling down, steady rhythmic pulse, remaining hopeful but less intense, transition to slightly edgier texture, 100 BPM.",
        "duration": 29,
        "phase": "Breakthrough"
    },
    6: {
        "name": "Punk Intro",
        "prompt": "Driving rhythmic bassline, fast-paced drums, new-wave energy, clean electric guitar strumming (no distortion), high energy pulse, 120 BPM, mysterious and cool.",
        "duration": 26,
        "phase": "Punk Revolution"
    },
    7: {
        "name": "Inflection 2: The Energy Peak",
        "prompt": "High energy alternative rock, driving drum beat, catchy bass groove, upbeat and rebellious but polished, The Sugarcubes style, dynamic and fast, 125 BPM, no harsh noise, smooth but powerful.",
        "duration": 35,
        "phase": "Punk Revolution"
    },
    8: {
        "name": "Punk Fade Out",
        "prompt": "Rhythmic drum groove continues, bassline becomes simpler, atmospheric synthesizers entering, cooling down energy, transition towards electronic pop, 120 BPM.",
        "duration": 45,
        "phase": "Punk Revolution"
    },
    9: {
        "name": "Inflection 3: The Global Anthem",
        "prompt": "Anthemic electronic pop, 90s house beat, sophisticated synthesizer, celebratory and majestic, wide stadium sound, confident and polished, artistic freedom, 128 BPM, euphoric finale.",
        "duration": 148,
        "phase": "Global Mastery"
    }
}
