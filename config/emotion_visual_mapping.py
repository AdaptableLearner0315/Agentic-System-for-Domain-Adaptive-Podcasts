"""
Emotion-Visual Mapping Configuration
Author: Sarath

Maps emotions to visual characteristics for image generation.
Used by VisualEnhancerAgent to create emotionally-aligned image prompts.

Each emotion defines:
- color_palette: Color descriptors for the image
- lighting: Lighting style and quality
- mood: Atmospheric and emotional descriptors
- composition: Framing and compositional guidance
"""

# Emotion to visual style mapping
EMOTION_VISUAL_STYLE = {
    "wonder": {
        "color_palette": "soft blues, ethereal whites, subtle golds, luminous highlights",
        "lighting": "diffused magical light, soft rays through clouds, gentle dawn glow",
        "mood": "dreamlike, expansive, serene, awe-inspiring",
        "composition": "wide shots, vast horizons, upward angles, expansive negative space",
        "atmosphere": "misty, ethereal, otherworldly"
    },
    "curiosity": {
        "color_palette": "warm amber, soft yellows, natural earth tones",
        "lighting": "warm natural light, dappled sunlight, inviting illumination",
        "mood": "inviting, exploratory, engaging, inquisitive",
        "composition": "medium shots, leading lines, points of interest, depth layers",
        "atmosphere": "welcoming, intriguing, layered"
    },
    "tension": {
        "color_palette": "deep shadows, stark contrasts, cold blues, muted tones",
        "lighting": "dramatic harsh angles, silhouettes, chiaroscuro, low-key lighting",
        "mood": "suspenseful, claustrophobic, anticipatory, uneasy",
        "composition": "tight framing, sharp angles, close perspectives, off-balance",
        "atmosphere": "ominous, charged, unstable"
    },
    "triumph": {
        "color_palette": "warm golds, rich oranges, bright highlights, victorious reds",
        "lighting": "golden hour backlit, radiant, heroic rim lighting",
        "mood": "victorious, uplifting, powerful, celebratory",
        "composition": "heroic low angles, open composition, symmetry, epic scale",
        "atmosphere": "glorious, triumphant, expansive"
    },
    "melancholy": {
        "color_palette": "muted blues, soft grays, desaturated tones, rain-washed colors",
        "lighting": "overcast diffused light, soft shadows, gentle twilight",
        "mood": "reflective, somber, wistful, nostalgic sadness",
        "composition": "intimate framing, isolated subjects, empty spaces, downward gaze",
        "atmosphere": "quiet, contemplative, heavy"
    },
    "intrigue": {
        "color_palette": "deep purples, mysterious blues, subtle gold accents, shadow play",
        "lighting": "partial illumination, dramatic shadows, selective highlights",
        "mood": "mysterious, compelling, secretive, alluring",
        "composition": "partially revealed subjects, shadows obscuring details, depth",
        "atmosphere": "enigmatic, captivating, hidden depths"
    },
    "excitement": {
        "color_palette": "vibrant warm colors, energetic contrasts, electric highlights",
        "lighting": "bright dynamic lighting, stage lights, vivid illumination",
        "mood": "energetic, thrilling, dynamic, alive",
        "composition": "dynamic angles, motion blur suggestion, action framing",
        "atmosphere": "electric, buzzing, alive with energy"
    },
    "reflection": {
        "color_palette": "soft sepia tones, warm neutrals, gentle faded colors",
        "lighting": "soft window light, contemplative glow, gentle ambient",
        "mood": "thoughtful, meditative, peaceful, introspective",
        "composition": "centered subjects, calm symmetry, still waters, mirrors",
        "atmosphere": "quiet, peaceful, timeless"
    },
    "restlessness": {
        "color_palette": "unsettled contrasts, edgy colors, urban grays with neon accents",
        "lighting": "flickering, unstable, harsh street lights",
        "mood": "uneasy, searching, dissatisfied, yearning",
        "composition": "off-center subjects, tilted horizons, crowded frames",
        "atmosphere": "agitated, unsettled, seeking"
    },
    "explosive_energy": {
        "color_palette": "vivid reds, intense oranges, electric whites, high contrast",
        "lighting": "dramatic strobes, explosive highlights, high-energy illumination",
        "mood": "powerful, overwhelming, intense, raw power",
        "composition": "extreme angles, close-ups, motion explosion, radial energy",
        "atmosphere": "volcanic, unstoppable, primal force"
    },
    "rebellion": {
        "color_palette": "dark shadows, punk red accents, gritty urban tones",
        "lighting": "harsh underground lighting, DIY aesthetic, raw illumination",
        "mood": "defiant, raw, authentic, anti-establishment",
        "composition": "confrontational angles, tight crops, urban decay backdrop",
        "atmosphere": "underground, fierce, uncompromising"
    },
    "liberation": {
        "color_palette": "open sky blues, freedom whites, hopeful yellows, rising dawn",
        "lighting": "bright open light, breaking through clouds, liberating rays",
        "mood": "free, unburdened, joyful release, breaking chains",
        "composition": "open horizons, upward movement, breaking barriers, flight",
        "atmosphere": "soaring, free, boundless"
    },
    "experimentation": {
        "color_palette": "unusual color combinations, unexpected contrasts, artistic palette",
        "lighting": "creative lighting, unconventional sources, artistic shadows",
        "mood": "creative, boundary-pushing, innovative, playful risk",
        "composition": "unconventional framing, rule-breaking, artistic abstraction",
        "atmosphere": "creative laboratory, anything possible"
    },
    "mastery": {
        "color_palette": "rich sophisticated tones, elegant contrasts, refined palette",
        "lighting": "professional studio lighting, polished illumination, expert control",
        "mood": "confident, accomplished, authoritative, peak performance",
        "composition": "balanced mastery, controlled precision, elegant framing",
        "atmosphere": "professional, accomplished, pinnacle"
    },
    "intensity": {
        "color_palette": "saturated colors, high contrast, focused highlights",
        "lighting": "focused spotlight, dramatic concentration, laser precision",
        "mood": "focused, driven, unrelenting, laser-like attention",
        "composition": "tight focus, shallow depth, subject dominance",
        "atmosphere": "concentrated, unwavering, powerful presence"
    },
    "neutral": {
        "color_palette": "balanced natural tones, documentary colors",
        "lighting": "natural balanced lighting, documentary style",
        "mood": "neutral, objective, documentary",
        "composition": "standard documentary framing",
        "atmosphere": "neutral, balanced"
    }
}


def get_emotion_visual_style(emotion: str) -> dict:
    """
    Get visual style parameters for a specific emotion.

    Args:
        emotion: Emotion name (case-insensitive)

    Returns:
        Visual style dictionary with color_palette, lighting, mood, composition, atmosphere
    """
    return EMOTION_VISUAL_STYLE.get(emotion.lower(), EMOTION_VISUAL_STYLE["neutral"])


def build_emotion_prompt_suffix(emotion: str) -> str:
    """
    Build a prompt suffix string from emotion visual style.

    Args:
        emotion: Emotion name

    Returns:
        Formatted string to append to image prompts
    """
    style = get_emotion_visual_style(emotion)

    parts = [
        f"{style['mood']} atmosphere",
        f"{style['color_palette']}",
        f"{style['lighting']}",
        f"{style['composition']}"
    ]

    return ", ".join(parts)


def get_emotion_color_hint(emotion: str) -> str:
    """
    Get just the color palette for an emotion.

    Args:
        emotion: Emotion name

    Returns:
        Color palette description string
    """
    style = get_emotion_visual_style(emotion)
    return style.get("color_palette", "balanced natural tones")


def get_emotion_mood_hint(emotion: str) -> str:
    """
    Get just the mood descriptor for an emotion.

    Args:
        emotion: Emotion name

    Returns:
        Mood description string
    """
    style = get_emotion_visual_style(emotion)
    return style.get("mood", "neutral")


# Emotion progression suggestions for visual continuity
EMOTION_VISUAL_TRANSITIONS = {
    ("wonder", "curiosity"): "gradual warming of colors, light becoming more inviting",
    ("curiosity", "tension"): "colors cooling, shadows deepening, light narrowing",
    ("tension", "triumph"): "dramatic breakthrough of warm light, shadows retreating",
    ("melancholy", "reflection"): "subtle shift from cold to warm tones",
    ("restlessness", "rebellion"): "urban grays intensifying, accent colors sharpening",
    ("rebellion", "liberation"): "darkness breaking into light, confined to open",
    ("experimentation", "mastery"): "creative chaos organizing into elegant control",
}


def get_transition_hint(from_emotion: str, to_emotion: str) -> str:
    """
    Get visual transition guidance between two emotions.

    Args:
        from_emotion: Starting emotion
        to_emotion: Ending emotion

    Returns:
        Transition description or default guidance
    """
    key = (from_emotion.lower(), to_emotion.lower())
    return EMOTION_VISUAL_TRANSITIONS.get(
        key,
        "smooth visual progression maintaining narrative continuity"
    )


# List of supported emotions
SUPPORTED_VISUAL_EMOTIONS = list(EMOTION_VISUAL_STYLE.keys())


__all__ = [
    'EMOTION_VISUAL_STYLE',
    'EMOTION_VISUAL_TRANSITIONS',
    'SUPPORTED_VISUAL_EMOTIONS',
    'get_emotion_visual_style',
    'build_emotion_prompt_suffix',
    'get_emotion_color_hint',
    'get_emotion_mood_hint',
    'get_transition_hint',
]
