"""
Era Aesthetic Profiles for Series Generation
Author: Sarath

Defines the aesthetic DNA for different eras, including music, voice, visual,
and language profiles. Used by IntentAnalyzer to generate StyleDNA.
"""

from typing import Dict, Any

# Era aesthetic profiles - automatically detected from user prompts
ERA_PROFILES: Dict[str, Dict[str, Any]] = {
    "1960s": {
        "name": "The Sixties",
        "description": "Folk guitars, psychedelic, Beatles-esque sounds with earnest narration",
        "music_profile": {
            "instruments": ["acoustic guitar", "harmonica", "folk strings", "psychedelic organs"],
            "tempo": "moderate to upbeat",
            "mood": "idealistic, hopeful, revolutionary",
            "style_hints": ["folk rock", "psychedelia", "protest songs", "British Invasion"],
            "bgm_prompt_prefix": "1960s folk-rock, acoustic guitars, warm analog recording,"
        },
        "voice_profile": {
            "style": "earnest",
            "pacing": "measured, theatrical",
            "warmth": "high",
            "energy": "passionate",
            "reference": "Cronkite-style broadcast, thoughtful delivery",
            "tts_hints": {"speed": 0.95, "stability": 0.7}
        },
        "visual_profile": {
            "colors": ["muted pastels", "earth tones", "psychedelic swirls"],
            "textures": ["film grain", "faded photographs", "Polaroid edges"],
            "aesthetic": "vintage documentary, newsreel footage style",
            "prompt_suffix": "1960s aesthetic, vintage film grain, muted colors, documentary style"
        },
        "language_profile": {
            "tone": "idealistic",
            "vocabulary": ["awakening", "revolution", "movement", "generation"],
            "sensory_emphasis": "visual and emotional",
            "sentence_style": "declarative, building momentum"
        }
    },

    "1970s": {
        "name": "The Seventies",
        "description": "Funk bass, disco strings, warm FM DJ voice with sensory storytelling",
        "music_profile": {
            "instruments": ["funk bass", "wah-wah guitar", "disco strings", "synth pads", "horns"],
            "tempo": "groovy, danceable",
            "mood": "warm, funky, expressive",
            "style_hints": ["funk", "disco", "soul", "progressive rock"],
            "bgm_prompt_prefix": "1970s funk and disco, groovy bass lines, warm analog synths,"
        },
        "voice_profile": {
            "style": "warm FM DJ",
            "pacing": "conversational, smooth",
            "warmth": "very high",
            "energy": "laid-back confidence",
            "reference": "late-night radio host, intimate storytelling",
            "tts_hints": {"speed": 0.9, "stability": 0.65}
        },
        "visual_profile": {
            "colors": ["orange", "gold", "brown", "burnt sienna", "avocado green"],
            "textures": ["shag carpet", "wood paneling", "neon lights"],
            "aesthetic": "warm, intimate, nightclub photography",
            "prompt_suffix": "1970s aesthetic, warm orange and gold tones, disco era, Studio 54 vibes"
        },
        "language_profile": {
            "tone": "sensory",
            "vocabulary": ["groove", "feel", "vibe", "soul", "expression"],
            "sensory_emphasis": "tactile and auditory",
            "sentence_style": "flowing, rhythmic, feel the groove"
        }
    },

    "1980s": {
        "name": "The Eighties",
        "description": "Synth pads, gated reverb, confident MTV VJ energy",
        "music_profile": {
            "instruments": ["synth pads", "drum machines", "gated reverb snare", "electric guitar"],
            "tempo": "driving, energetic",
            "mood": "bold, confident, futuristic",
            "style_hints": ["synth-pop", "new wave", "hair metal", "electronic"],
            "bgm_prompt_prefix": "1980s synth-pop, dramatic reverb, electronic drums, bold production,"
        },
        "voice_profile": {
            "style": "confident MTV VJ",
            "pacing": "upbeat, punchy",
            "warmth": "medium",
            "energy": "high, enthusiastic",
            "reference": "MTV presenter, infomercial energy",
            "tts_hints": {"speed": 1.05, "stability": 0.75}
        },
        "visual_profile": {
            "colors": ["neon pink", "electric cyan", "chrome", "black"],
            "textures": ["chrome surfaces", "VHS scan lines", "laser grids"],
            "aesthetic": "MTV era, music video style, bold graphics",
            "prompt_suffix": "1980s aesthetic, neon colors, chrome accents, MTV era visuals"
        },
        "language_profile": {
            "tone": "bold, superlative",
            "vocabulary": ["extreme", "ultimate", "radical", "mega", "power"],
            "sensory_emphasis": "visual spectacle",
            "sentence_style": "punchy, exclamatory, high energy"
        }
    },

    "1990s": {
        "name": "The Nineties",
        "description": "Grunge guitars, trip-hop beats, authentic alternative voice",
        "music_profile": {
            "instruments": ["distorted guitars", "breakbeats", "trip-hop samples", "ambient pads"],
            "tempo": "varied, dynamic",
            "mood": "authentic, raw, introspective",
            "style_hints": ["grunge", "trip-hop", "alternative rock", "electronica"],
            "bgm_prompt_prefix": "1990s alternative, raw guitars, trip-hop elements, authentic sound,"
        },
        "voice_profile": {
            "style": "authentic, unpolished",
            "pacing": "natural, varied",
            "warmth": "medium-low",
            "energy": "subdued intensity",
            "reference": "indie documentary narrator, real and unfiltered",
            "tts_hints": {"speed": 1.0, "stability": 0.6}
        },
        "visual_profile": {
            "colors": ["flannel patterns", "muted earth tones", "industrial grays"],
            "textures": ["grainy video", "handheld camera", "concert photography"],
            "aesthetic": "documentary realism, anti-gloss",
            "prompt_suffix": "1990s aesthetic, grainy documentary style, raw and authentic"
        },
        "language_profile": {
            "tone": "authentic, ironic",
            "vocabulary": ["real", "alternative", "underground", "raw"],
            "sensory_emphasis": "emotional authenticity",
            "sentence_style": "conversational, questioning, introspective"
        }
    },

    "2000s": {
        "name": "The Aughts",
        "description": "Digital production, polished pop, professional broadcast quality",
        "music_profile": {
            "instruments": ["digital synths", "auto-tune", "808 drums", "crisp guitars"],
            "tempo": "polished, pop-friendly",
            "mood": "clean, professional, optimistic",
            "style_hints": ["pop-rock", "R&B", "hip-hop", "indie rock"],
            "bgm_prompt_prefix": "2000s pop production, clean digital sound, polished and professional,"
        },
        "voice_profile": {
            "style": "professional broadcast",
            "pacing": "crisp, clear",
            "warmth": "medium",
            "energy": "controlled enthusiasm",
            "reference": "network television host, polished delivery",
            "tts_hints": {"speed": 1.0, "stability": 0.8}
        },
        "visual_profile": {
            "colors": ["bright whites", "clean blues", "chrome silver"],
            "textures": ["digital clarity", "web 2.0 gradients", "glossy surfaces"],
            "aesthetic": "HD broadcast, digital polish",
            "prompt_suffix": "2000s aesthetic, crisp digital imagery, clean and polished"
        },
        "language_profile": {
            "tone": "optimistic, connected",
            "vocabulary": ["viral", "global", "connected", "digital", "revolutionary"],
            "sensory_emphasis": "visual clarity",
            "sentence_style": "informative, enthusiastic, forward-looking"
        }
    },

    "retro": {
        "name": "Retro/Vintage",
        "description": "Jazz samples, vinyl crackle, intimate fireside storytelling",
        "music_profile": {
            "instruments": ["jazz samples", "vinyl crackle", "tape warmth", "brushed drums"],
            "tempo": "relaxed, intimate",
            "mood": "wistful, nostalgic, warm",
            "style_hints": ["lo-fi", "jazz", "easy listening", "vintage recordings"],
            "bgm_prompt_prefix": "vintage jazz, vinyl warmth, lo-fi aesthetic, nostalgic and intimate,"
        },
        "voice_profile": {
            "style": "intimate, lo-fi",
            "pacing": "slow, deliberate",
            "warmth": "very high",
            "energy": "calm, reflective",
            "reference": "fireside storyteller, late-night radio",
            "tts_hints": {"speed": 0.85, "stability": 0.6}
        },
        "visual_profile": {
            "colors": ["sepia", "cream", "faded colors", "warm browns"],
            "textures": ["faded photographs", "film scratches", "vignette edges"],
            "aesthetic": "old photographs, memory fragments",
            "prompt_suffix": "vintage aesthetic, sepia tones, faded photograph style, nostalgic"
        },
        "language_profile": {
            "tone": "wistful, nostalgic",
            "vocabulary": ["remember", "once", "those days", "used to be", "time"],
            "sensory_emphasis": "memory and emotion",
            "sentence_style": "reflective, poetic, meandering"
        }
    },

    "modern": {
        "name": "Modern/Contemporary",
        "description": "Lo-fi beats, ambient textures, natural NPR-style narration",
        "music_profile": {
            "instruments": ["lo-fi beats", "ambient pads", "minimal piano", "subtle electronics"],
            "tempo": "moderate, accessible",
            "mood": "calm, informative, accessible",
            "style_hints": ["lo-fi hip-hop", "ambient", "podcast music", "indie folk"],
            "bgm_prompt_prefix": "modern podcast music, lo-fi beats, ambient and accessible,"
        },
        "voice_profile": {
            "style": "natural NPR",
            "pacing": "conversational, clear",
            "warmth": "medium-high",
            "energy": "engaged but calm",
            "reference": "NPR host, conversational storytelling",
            "tts_hints": {"speed": 1.0, "stability": 0.7}
        },
        "visual_profile": {
            "colors": ["clean whites", "soft gradients", "muted pastels"],
            "textures": ["minimal design", "flat colors", "clean typography"],
            "aesthetic": "modern design, editorial photography",
            "prompt_suffix": "modern aesthetic, clean minimal design, contemporary photography style"
        },
        "language_profile": {
            "tone": "direct, accessible",
            "vocabulary": ["today", "now", "we", "understand", "explore"],
            "sensory_emphasis": "clarity and connection",
            "sentence_style": "clear, direct, conversational"
        }
    },

    "futuristic": {
        "name": "Futuristic/Sci-Fi",
        "description": "Glitchy electronics, sci-fi atmospheres, precise AI-adjacent narration",
        "music_profile": {
            "instruments": ["glitchy electronics", "sci-fi synths", "processed sounds", "digital textures"],
            "tempo": "varied, unpredictable",
            "mood": "mysterious, speculative, otherworldly",
            "style_hints": ["ambient electronic", "glitch", "sci-fi soundtrack", "experimental"],
            "bgm_prompt_prefix": "futuristic electronic music, sci-fi atmospheres, glitchy textures,"
        },
        "voice_profile": {
            "style": "precise, AI-adjacent",
            "pacing": "measured, deliberate",
            "warmth": "low",
            "energy": "controlled, mysterious",
            "reference": "documentary narrator from the future, calm precision",
            "tts_hints": {"speed": 0.95, "stability": 0.85}
        },
        "visual_profile": {
            "colors": ["deep blues", "electric purple", "holographic gradients"],
            "textures": ["holographic", "digital glitches", "data visualization"],
            "aesthetic": "sci-fi concept art, data visualization",
            "prompt_suffix": "futuristic aesthetic, sci-fi visuals, holographic effects, digital art"
        },
        "language_profile": {
            "tone": "speculative, precise",
            "vocabulary": ["imagine", "beyond", "possibility", "emergence", "transformation"],
            "sensory_emphasis": "conceptual and visual",
            "sentence_style": "precise, questioning, forward-looking"
        }
    }
}


# Era detection keywords - map keywords in prompts to eras
ERA_KEYWORDS: Dict[str, list] = {
    "1960s": ["1960s", "60s", "sixties", "beatles", "woodstock", "vietnam", "civil rights",
              "counterculture", "hippie", "psychedelic", "jfk", "kennedy"],
    "1970s": ["1970s", "70s", "seventies", "disco", "funk", "studio 54", "nixon", "watergate",
              "punk", "glam rock", "motown", "bee gees"],
    "1980s": ["1980s", "80s", "eighties", "synth", "mtv", "reagan", "new wave", "hair metal",
              "synthpop", "cold war", "wall street", "arcade"],
    "1990s": ["1990s", "90s", "nineties", "grunge", "nirvana", "internet", "dot com",
              "alternative", "hip hop golden age", "seattle", "clinton"],
    "2000s": ["2000s", "00s", "aughts", "ipod", "myspace", "war on terror", "obama",
              "social media", "smartphones", "youtube"],
    "retro": ["retro", "vintage", "classic", "golden age", "old school", "nostalgic",
              "yesteryear", "bygone", "timeless"],
    "modern": ["modern", "contemporary", "today", "current", "present day", "recent",
               "21st century", "now"],
    "futuristic": ["futuristic", "future", "sci-fi", "science fiction", "2050", "tomorrow",
                   "next century", "speculative", "cyberpunk", "post-human"]
}


def get_era_profile(era: str) -> Dict[str, Any]:
    """Get the aesthetic profile for an era."""
    return ERA_PROFILES.get(era.lower(), ERA_PROFILES["modern"])


def detect_era_from_text(text: str) -> str:
    """Detect era from text based on keywords. Returns 'modern' if no match."""
    text_lower = text.lower()

    for era, keywords in ERA_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return era

    return "modern"


def get_all_eras() -> list:
    """Get list of all available eras."""
    return list(ERA_PROFILES.keys())
