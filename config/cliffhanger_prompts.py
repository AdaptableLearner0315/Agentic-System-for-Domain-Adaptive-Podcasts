"""
Cliffhanger Prompts and Strategies
Author: Sarath

Defines LLM prompts and audio generation prompts for each cliffhanger type.
These create the "can't stop listening" effect in episodic series.
"""

from typing import Dict, Any

# Cliffhanger types with their mechanics and generation prompts
CLIFFHANGER_TYPES: Dict[str, Dict[str, Any]] = {
    "revelation": {
        "name": "The Revelation",
        "description": "Stop mid-disclosure. Give JUST enough to create burning curiosity.",
        "tension_level": "high",
        "mechanic": "Reveal something shocking but stop before explaining its significance",
        "best_for": ["mystery", "investigation", "biography", "music_history"],

        "llm_prompt": """Generate a REVELATION cliffhanger for this episode.

MECHANICS:
- Stop mid-disclosure
- Give JUST enough to create burning curiosity
- Don't explain what it means yet
- The audience should feel they're ONE STEP from understanding

EXAMPLE PATTERNS:
- "She unfolded the letter. Her hands began to shake. The first line read: 'I know what you did on June 14th, 1977.'"
- "The document was authentic. The signature at the bottom was unmistakable. It belonged to..."
- "Hidden in the recording, engineers discovered something no one had noticed for 40 years..."

Based on the episode content below, write a 2-3 sentence revelation cliffhanger.
End MID-REVELATION. The listener should be desperate to know what comes next.

Episode content:
{content}

Write ONLY the cliffhanger text, no preamble.""",

        "audio_sting": {
            "description": "Sustained chord slowly fading, lingering mystery",
            "duration_seconds": 4,
            "bgm_prompt": "dramatic sustained orchestral chord, slow fade, mysterious ending, cinematic reveal moment, lingering tension"
        }
    },

    "twist": {
        "name": "The Twist",
        "description": "Recontextualize everything. End IMMEDIATELY after twist lands.",
        "tension_level": "maximum",
        "mechanic": "Reveal information that changes the meaning of everything before it",
        "best_for": ["true_crime", "narrative_fiction", "documentary"],

        "llm_prompt": """Generate a TWIST cliffhanger for this episode.

MECHANICS:
- Recontextualize everything the listener thought they knew
- End IMMEDIATELY after the twist lands
- No explanation, no softening - just the twist and silence
- Maximum impact in minimum words

EXAMPLE PATTERNS:
- "The detective saw it. The handwriting on the hotel register... it was identical to the ransom note."
- "DNA results came back. The victim wasn't who everyone thought she was."
- "That's when investigators realized: the person calling for help was the same person who..."

Based on the episode content below, write a 1-2 sentence twist cliffhanger.
End IMMEDIATELY after the twist. No cushioning.

Episode content:
{content}

Write ONLY the cliffhanger text, no preamble.""",

        "audio_sting": {
            "description": "Dramatic hit followed by dead silence",
            "duration_seconds": 3,
            "bgm_prompt": "dramatic orchestral hit, sudden stop, dead silence, shocking reveal, impact moment then nothing"
        }
    },

    "question": {
        "name": "The Question",
        "description": "Pose a specific, concrete question. Make the listener feel close to answering.",
        "tension_level": "medium-high",
        "mechanic": "Ask a question the listener desperately wants answered, that feels almost solvable",
        "best_for": ["documentary", "science", "investigation", "true_crime"],

        "llm_prompt": """Generate a QUESTION cliffhanger for this episode.

MECHANICS:
- Pose a specific, concrete question (not vague)
- Make the listener feel they're CLOSE to figuring it out
- The question should be answerable but tantalizingly out of reach
- Often involves contradictions or impossible math

EXAMPLE PATTERNS:
- "If she was at the restaurant at 9pm, and the murder was at 9:15, 45 minutes away... how is her fingerprint on the weapon?"
- "The recording was made in 1965. But the technology to create that sound didn't exist until 1978. How?"
- "Everyone remembers where they were that day. But no one can explain why the official timeline has a 47-minute gap."

Based on the episode content below, write a 2-3 sentence question cliffhanger.
End with a question that feels ALMOST answerable.

Episode content:
{content}

Write ONLY the cliffhanger text, no preamble.""",

        "audio_sting": {
            "description": "Unresolved piano phrase, questioning",
            "duration_seconds": 3,
            "bgm_prompt": "unresolved piano chord, questioning tone, suspended tension, incomplete musical phrase, mystery underscore"
        }
    },

    "countdown": {
        "name": "The Countdown",
        "description": "Create urgency. Time is running out. Impossible math.",
        "tension_level": "high",
        "mechanic": "Establish a deadline and make it seem impossible to meet",
        "best_for": ["historical_drama", "crisis_narratives", "documentary", "narrative_fiction"],

        "llm_prompt": """Generate a COUNTDOWN cliffhanger for this episode.

MECHANICS:
- Create urgency with specific time constraints
- Make the math feel impossible
- The clock is ticking, stakes are real
- Compress time to create maximum pressure

EXAMPLE PATTERNS:
- "They had 47 hours. It was now 5:47 AM. The launch was at 6:00 AM. The fix would take 20 minutes."
- "The deadline was midnight. Three hours away. And they still hadn't found the one piece of evidence that could save everything."
- "In 72 hours, the world would know. And they had exactly that long to decide: reveal the truth, or bury it forever."

Based on the episode content below, write a 2-3 sentence countdown cliffhanger.
Create URGENCY. Make time feel like it's running out.

Episode content:
{content}

Write ONLY the cliffhanger text, no preamble.""",

        "audio_sting": {
            "description": "Accelerating tick, building tension, abrupt cut",
            "duration_seconds": 4,
            "bgm_prompt": "accelerating clock tick, building orchestral tension, urgent countdown, dramatic crescendo then abrupt stop"
        }
    },

    "promise": {
        "name": "The Promise",
        "description": "Explicitly promise something amazing. Use narrator authority.",
        "tension_level": "medium",
        "mechanic": "Narrator breaks frame to promise the listener something remarkable is coming",
        "best_for": ["investigative", "building_to_climax", "documentary", "biography"],

        "llm_prompt": """Generate a PROMISE cliffhanger for this episode.

MECHANICS:
- The narrator explicitly promises something amazing
- Break the fourth wall slightly - speak directly to the listener
- Use your authority as storyteller to build anticipation
- The promise should be specific enough to create real excitement

EXAMPLE PATTERNS:
- "What happens next is why I wanted to tell this story. It involves a letter hidden for forty years, and a secret that changes everything."
- "We've covered the setup. Now comes the part that will make you understand why this story matters."
- "I've been waiting to tell you this part. What {person} did next is something no one saw coming. And it's about to change your understanding of everything."

Based on the episode content below, write a 2-3 sentence promise cliffhanger.
Make a PROMISE to the listener about what's coming.

Episode content:
{content}

Write ONLY the cliffhanger text, no preamble.""",

        "audio_sting": {
            "description": "Building anticipation, stops at peak",
            "duration_seconds": 4,
            "bgm_prompt": "building anticipation music, rising strings, crescendo that stops at peak, exciting promise, dramatic pause before payoff"
        }
    }
}


# Cliffhanger placement strategy by series length
CLIFFHANGER_STRATEGIES: Dict[int, list] = {
    3: [
        {"episode": 1, "type": "revelation", "purpose": "Hook hard, create central mystery"},
        {"episode": 2, "type": "twist", "purpose": "Mid-series shock, highest tension"},
        # Episode 3 is finale - resolution, no cliffhanger needed
    ],
    4: [
        {"episode": 1, "type": "revelation", "purpose": "Hook hard, create central mystery"},
        {"episode": 2, "type": "question", "purpose": "Deepen engagement, intellectual"},
        {"episode": 3, "type": "countdown", "purpose": "Drive to finale, urgency"},
        # Episode 4 is finale
    ],
    5: [
        {"episode": 1, "type": "revelation", "purpose": "Hook hard, create central mystery"},
        {"episode": 2, "type": "question", "purpose": "Deepen engagement, intellectual"},
        {"episode": 3, "type": "twist", "purpose": "Mid-series shock, highest tension"},
        {"episode": 4, "type": "countdown", "purpose": "Drive to finale, urgency"},
        # Episode 5 is finale
    ],
    6: [
        {"episode": 1, "type": "revelation", "purpose": "Hook hard, create central mystery"},
        {"episode": 2, "type": "question", "purpose": "Deepen engagement"},
        {"episode": 3, "type": "promise", "purpose": "Build anticipation mid-series"},
        {"episode": 4, "type": "twist", "purpose": "Late-series shock"},
        {"episode": 5, "type": "countdown", "purpose": "Drive to finale"},
        # Episode 6 is finale
    ],
    # Default pattern for 7+ episodes
    "default": [
        {"position": 0.0, "type": "revelation", "purpose": "Hook hard"},
        {"position": 0.25, "type": "question", "purpose": "Deepen engagement"},
        {"position": 0.5, "type": "twist", "purpose": "Mid-series shock"},
        {"position": 0.75, "type": "countdown", "purpose": "Build to finale"},
    ]
}


def get_cliffhanger_type(type_name: str) -> Dict[str, Any]:
    """Get cliffhanger definition by type name."""
    return CLIFFHANGER_TYPES.get(type_name.lower(), CLIFFHANGER_TYPES["question"])


def get_cliffhanger_prompt(type_name: str, content: str) -> str:
    """Get formatted LLM prompt for generating a specific cliffhanger type."""
    cliffhanger = get_cliffhanger_type(type_name)
    return cliffhanger["llm_prompt"].format(content=content)


def get_audio_sting_prompt(type_name: str) -> str:
    """Get BGM prompt for generating cliffhanger audio sting."""
    cliffhanger = get_cliffhanger_type(type_name)
    return cliffhanger["audio_sting"]["bgm_prompt"]


def get_cliffhanger_strategy(episode_count: int) -> list:
    """Get cliffhanger placement strategy for a series length."""
    if episode_count in CLIFFHANGER_STRATEGIES:
        return CLIFFHANGER_STRATEGIES[episode_count]

    # For series longer than 6 episodes, use position-based strategy
    default = CLIFFHANGER_STRATEGIES["default"]
    strategy = []

    for item in default:
        episode = int(item["position"] * (episode_count - 1)) + 1
        strategy.append({
            "episode": episode,
            "type": item["type"],
            "purpose": item["purpose"]
        })

    return strategy


def get_episode_cliffhanger_type(episode_number: int, total_episodes: int, genre: str = None) -> str:
    """Determine the best cliffhanger type for a specific episode position."""
    # Finale episodes don't need cliffhangers (return resolution placeholder)
    if episode_number >= total_episodes:
        return None

    strategy = get_cliffhanger_strategy(total_episodes)

    for item in strategy:
        if item["episode"] == episode_number:
            return item["type"]

    # Default fallback
    return "question"


# "Previously on..." narration styles
PREVIOUSLY_ON_STYLES: Dict[str, str] = {
    "emotional": """Write a "Previously on..." narration that rebuilds EMOTIONAL stakes.
Don't just summarize plot - remind the listener WHY they should care.
Include the emotional state we left off in, the tension that was building.
15-25 seconds when spoken. Focus on feeling, not facts.""",

    "tension": """Write a "Previously on..." narration that rebuilds TENSION.
Reference the cliffhanger from last episode. Make the listener feel that urgency again.
Don't resolve anything - deepen the mystery. Create immediate engagement.
15-25 seconds when spoken.""",

    "callback": """Write a "Previously on..." narration that references MULTIPLE earlier episodes.
Reward the binge listener by connecting threads. Show how elements are coming together.
Build anticipation by showing how far we've come.
15-25 seconds when spoken."""
}


def get_previously_on_prompt(style: str = "tension") -> str:
    """Get the prompt style for generating 'Previously on' narration."""
    return PREVIOUSLY_ON_STYLES.get(style, PREVIOUSLY_ON_STYLES["tension"])
