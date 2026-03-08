"""
Genre DNA Templates for Series Generation
Author: Sarath

Defines structural templates for different podcast genres including
narrative arcs, cliffhanger strategies, and thematic patterns.
"""

from typing import Dict, Any, List

# Genre DNA templates - structure and storytelling patterns for each genre
GENRE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "music_history": {
        "name": "Music History",
        "description": "Chronicles of musical movements, artists, and cultural impact",
        "arc_templates": {
            "rise_and_fall": {
                "description": "The classic trajectory of a movement or artist",
                "episode_structure": [
                    {"position": 0.2, "beat": "origins", "description": "Where it all began"},
                    {"position": 0.4, "beat": "rise", "description": "The breakthrough moment"},
                    {"position": 0.6, "beat": "peak", "description": "At the height of power/fame"},
                    {"position": 0.8, "beat": "fall", "description": "The decline or transformation"},
                    {"position": 1.0, "beat": "legacy", "description": "What remains, what changed"}
                ]
            },
            "evolution": {
                "description": "How a genre or sound transformed over time",
                "episode_structure": [
                    {"position": 0.2, "beat": "roots", "description": "The foundation"},
                    {"position": 0.4, "beat": "innovation", "description": "Key innovations"},
                    {"position": 0.6, "beat": "explosion", "description": "Mainstream breakthrough"},
                    {"position": 0.8, "beat": "fragmentation", "description": "Sub-genres emerge"},
                    {"position": 1.0, "beat": "present", "description": "Where we are now"}
                ]
            }
        },
        "cliffhanger_strategies": ["revelation", "question", "promise"],
        "callback_types": ["artist_mention", "song_reference", "venue", "recording"],
        "thematic_elements": ["sound", "culture", "innovation", "influence", "controversy"],
        "language_cues": {
            "hook_starters": [
                "On a cold night in {city}, a sound was born that would change everything.",
                "Before {artist} walked into that studio, no one had heard anything like it.",
                "The year was {year}. Music was about to be revolutionized."
            ],
            "transition_phrases": [
                "But the music was only part of the story.",
                "What happened next would shock the industry.",
                "Behind the scenes, something else was brewing."
            ]
        }
    },

    "true_crime": {
        "name": "True Crime",
        "description": "Investigations, mysteries, and the pursuit of justice",
        "arc_templates": {
            "investigation": {
                "description": "Following the trail of evidence",
                "episode_structure": [
                    {"position": 0.15, "beat": "crime", "description": "The inciting incident"},
                    {"position": 0.35, "beat": "suspects", "description": "Who could have done it?"},
                    {"position": 0.55, "beat": "twists", "description": "Nothing is as it seems"},
                    {"position": 0.75, "beat": "breakthrough", "description": "The key discovery"},
                    {"position": 1.0, "beat": "resolution", "description": "Justice or mystery"}
                ]
            },
            "mystery_reveal": {
                "description": "Peeling back layers of a complex case",
                "episode_structure": [
                    {"position": 0.2, "beat": "surface", "description": "What everyone knew"},
                    {"position": 0.4, "beat": "doubt", "description": "First cracks appear"},
                    {"position": 0.6, "beat": "hidden", "description": "Secret revelations"},
                    {"position": 0.8, "beat": "truth", "description": "The real story"},
                    {"position": 1.0, "beat": "aftermath", "description": "Living with the truth"}
                ]
            }
        },
        "cliffhanger_strategies": ["twist", "revelation", "question", "countdown"],
        "callback_types": ["evidence", "witness", "location", "timeline_detail"],
        "thematic_elements": ["evidence", "motive", "alibi", "psychology", "justice"],
        "language_cues": {
            "hook_starters": [
                "The call came in at {time}. What police found would haunt them for years.",
                "Everyone in {location} knew {victim}. No one knew who wanted them dead.",
                "The evidence pointed one direction. The truth pointed somewhere else entirely."
            ],
            "transition_phrases": [
                "But there was one detail that didn't add up.",
                "What investigators found next changed everything.",
                "And that's when the real mystery began."
            ]
        }
    },

    "biography": {
        "name": "Biography",
        "description": "The life story of a remarkable individual",
        "arc_templates": {
            "life_journey": {
                "description": "Cradle to legacy",
                "episode_structure": [
                    {"position": 0.15, "beat": "origins", "description": "Where they came from"},
                    {"position": 0.35, "beat": "formative", "description": "What shaped them"},
                    {"position": 0.55, "beat": "rise", "description": "The path to greatness"},
                    {"position": 0.75, "beat": "challenge", "description": "The greatest test"},
                    {"position": 1.0, "beat": "legacy", "description": "What they left behind"}
                ]
            },
            "pivotal_moment": {
                "description": "Building to the defining decision",
                "episode_structure": [
                    {"position": 0.2, "beat": "before", "description": "Life before the moment"},
                    {"position": 0.4, "beat": "pressure", "description": "Forces converging"},
                    {"position": 0.6, "beat": "decision", "description": "The critical choice"},
                    {"position": 0.8, "beat": "consequences", "description": "What followed"},
                    {"position": 1.0, "beat": "meaning", "description": "Why it mattered"}
                ]
            }
        },
        "cliffhanger_strategies": ["revelation", "promise", "question"],
        "callback_types": ["childhood_memory", "mentor", "rival", "quote", "artifact"],
        "thematic_elements": ["ambition", "sacrifice", "relationships", "legacy", "contradiction"],
        "language_cues": {
            "hook_starters": [
                "Before {name} became {achievement}, they were just {origin}.",
                "Everyone knows what {name} accomplished. Few know what it cost them.",
                "The moment that would define {name}'s life hadn't happened yet."
            ],
            "transition_phrases": [
                "But success would come at a price.",
                "What no one knew was the sacrifice behind the achievement.",
                "The public saw triumph. The private story was more complicated."
            ]
        }
    },

    "documentary": {
        "name": "Documentary",
        "description": "In-depth exploration of events, movements, or phenomena",
        "arc_templates": {
            "event_chronicle": {
                "description": "Understanding a pivotal event",
                "episode_structure": [
                    {"position": 0.15, "beat": "context", "description": "The world before"},
                    {"position": 0.35, "beat": "buildup", "description": "Tensions rising"},
                    {"position": 0.55, "beat": "event", "description": "What happened"},
                    {"position": 0.75, "beat": "aftermath", "description": "Immediate impact"},
                    {"position": 1.0, "beat": "legacy", "description": "Lasting change"}
                ]
            },
            "multi_perspective": {
                "description": "Same story, different views",
                "episode_structure": [
                    {"position": 0.2, "beat": "overview", "description": "The big picture"},
                    {"position": 0.4, "beat": "perspective_1", "description": "First viewpoint"},
                    {"position": 0.6, "beat": "perspective_2", "description": "Counter viewpoint"},
                    {"position": 0.8, "beat": "synthesis", "description": "Finding truth"},
                    {"position": 1.0, "beat": "meaning", "description": "What we learned"}
                ]
            }
        },
        "cliffhanger_strategies": ["question", "promise", "revelation"],
        "callback_types": ["archival_quote", "statistic", "expert_insight", "artifact"],
        "thematic_elements": ["cause_effect", "perspective", "evidence", "impact", "truth"],
        "language_cues": {
            "hook_starters": [
                "In {year}, the world was about to change. No one saw it coming.",
                "To understand what happened, we need to go back to {context}.",
                "The story you think you know is only part of the truth."
            ],
            "transition_phrases": [
                "What happened next would reshape the world.",
                "But the official story missed something crucial.",
                "The consequences were only beginning."
            ]
        }
    },

    "science": {
        "name": "Science/Explainer",
        "description": "Making complex topics accessible and fascinating",
        "arc_templates": {
            "discovery": {
                "description": "The journey to understanding",
                "episode_structure": [
                    {"position": 0.2, "beat": "mystery", "description": "The question"},
                    {"position": 0.4, "beat": "foundation", "description": "Building blocks"},
                    {"position": 0.6, "beat": "breakthrough", "description": "The eureka moment"},
                    {"position": 0.8, "beat": "implications", "description": "What it means"},
                    {"position": 1.0, "beat": "future", "description": "Where we go from here"}
                ]
            },
            "explainer": {
                "description": "Building understanding step by step",
                "episode_structure": [
                    {"position": 0.2, "beat": "question", "description": "Why this matters"},
                    {"position": 0.4, "beat": "basics", "description": "Fundamental concepts"},
                    {"position": 0.6, "beat": "deep_dive", "description": "The complex part"},
                    {"position": 0.8, "beat": "application", "description": "Real world use"},
                    {"position": 1.0, "beat": "wonder", "description": "Mind-expanding conclusion"}
                ]
            }
        },
        "cliffhanger_strategies": ["question", "promise", "revelation"],
        "callback_types": ["concept", "researcher", "experiment", "analogy"],
        "thematic_elements": ["curiosity", "evidence", "breakthrough", "application", "wonder"],
        "language_cues": {
            "hook_starters": [
                "For centuries, scientists wondered: {question}. The answer was stranger than fiction.",
                "What if everything you thought you knew about {topic} was wrong?",
                "In a lab in {location}, researchers discovered something that defied explanation."
            ],
            "transition_phrases": [
                "But scientists discovered something unexpected.",
                "The implications went far beyond the lab.",
                "And that led to an even bigger question."
            ]
        }
    },

    "narrative_fiction": {
        "name": "Narrative Fiction",
        "description": "Serialized storytelling with dramatic arcs",
        "arc_templates": {
            "hero_journey": {
                "description": "Classic transformation narrative",
                "episode_structure": [
                    {"position": 0.15, "beat": "ordinary_world", "description": "Life before"},
                    {"position": 0.35, "beat": "call", "description": "The disruption"},
                    {"position": 0.55, "beat": "trials", "description": "Tests and allies"},
                    {"position": 0.75, "beat": "ordeal", "description": "The ultimate challenge"},
                    {"position": 1.0, "beat": "return", "description": "Transformed"}
                ]
            },
            "mystery": {
                "description": "Unraveling secrets",
                "episode_structure": [
                    {"position": 0.2, "beat": "hook", "description": "The inciting mystery"},
                    {"position": 0.4, "beat": "investigation", "description": "Following clues"},
                    {"position": 0.6, "beat": "revelation", "description": "Major discovery"},
                    {"position": 0.8, "beat": "twist", "description": "Everything changes"},
                    {"position": 1.0, "beat": "resolution", "description": "Truth revealed"}
                ]
            }
        },
        "cliffhanger_strategies": ["twist", "countdown", "revelation", "question"],
        "callback_types": ["character", "object", "location", "dialogue", "prophecy"],
        "thematic_elements": ["conflict", "growth", "relationships", "mystery", "stakes"],
        "language_cues": {
            "hook_starters": [
                "The night it all changed, {character} had no idea what was coming.",
                "Three words would alter the course of everything: {phrase}.",
                "When {character} opened the door, the life they knew ended."
            ],
            "transition_phrases": [
                "But fate had other plans.",
                "What they didn't know would change everything.",
                "And in the shadows, something stirred."
            ]
        }
    }
}


# Genre detection keywords
GENRE_KEYWORDS: Dict[str, List[str]] = {
    "music_history": [
        "disco", "rock", "jazz", "hip hop", "punk", "electronic music", "classical",
        "band", "musician", "album", "record", "song", "guitar", "studio", "label",
        "genre", "sound", "music scene", "concert", "tour", "festival"
    ],
    "true_crime": [
        "murder", "crime", "investigation", "detective", "police", "case", "victim",
        "suspect", "evidence", "trial", "conviction", "unsolved", "mysterious death",
        "disappearance", "killer", "forensic", "cold case"
    ],
    "biography": [
        "life of", "story of", "biography", "born", "died", "legacy", "career",
        "personal life", "rise to fame", "early years", "achievements", "who was",
        "journey of", "how they became"
    ],
    "documentary": [
        "history of", "event", "movement", "revolution", "war", "crisis", "disaster",
        "cultural", "social", "political", "economic", "impact", "decade", "era",
        "phenomenon", "trend", "changed the world"
    ],
    "science": [
        "science", "scientific", "discovery", "research", "experiment", "theory",
        "how does", "why does", "explained", "understanding", "brain", "universe",
        "physics", "biology", "chemistry", "technology", "invention", "breakthrough"
    ],
    "narrative_fiction": [
        "story", "tale", "fiction", "character", "adventure", "drama", "thriller",
        "mystery", "fantasy", "imagine", "once upon", "fictional"
    ]
}


def get_genre_template(genre: str) -> Dict[str, Any]:
    """Get the template for a genre."""
    return GENRE_TEMPLATES.get(genre.lower(), GENRE_TEMPLATES["documentary"])


def detect_genre_from_text(text: str) -> str:
    """Detect genre from text based on keywords. Returns 'documentary' if no match."""
    text_lower = text.lower()

    # Count keyword matches for each genre
    scores = {}
    for genre, keywords in GENRE_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            scores[genre] = score

    if scores:
        return max(scores, key=scores.get)

    return "documentary"


def get_arc_template(genre: str, arc_type: str = None) -> Dict[str, Any]:
    """Get a specific arc template for a genre."""
    template = get_genre_template(genre)
    arcs = template.get("arc_templates", {})

    if arc_type and arc_type in arcs:
        return arcs[arc_type]

    # Return first arc as default
    return next(iter(arcs.values())) if arcs else {}


def get_all_genres() -> List[str]:
    """Get list of all available genres."""
    return list(GENRE_TEMPLATES.keys())


def get_cliffhanger_strategies(genre: str) -> List[str]:
    """Get recommended cliffhanger strategies for a genre."""
    template = get_genre_template(genre)
    return template.get("cliffhanger_strategies", ["question", "promise"])
