"""
Text Processing Utilities
Author: Sarath

Contains text preprocessing functions for TTS and script processing.
"""

import re

# Strong words that need intensity emphasis
STRONG_WORDS = {
    'wild', 'otherworldly', 'impossible', 'revolutionary', 'radical',
    'volcanic', 'defy', 'defied', 'extraordinary', 'unprecedented',
    'explosive', 'stunning', 'remarkable', 'incredible', 'triumph',
    'breakthrough', 'decisive', 'feral', 'electric', 'volatile',
    'dissonant', 'lightning', 'quicksilver', 'captivated', 'unheard'
}


def preprocess_text_for_tts(text: str) -> str:
    """
    Preprocess text to avoid TTS issues.
    - Convert numbers to words
    - Fix pronunciations (Bjork -> Byerk)
    - Handle hyphens that might cause pauses

    Args:
        text: Raw text to preprocess

    Returns:
        Preprocessed text suitable for TTS
    """
    # Convert number patterns
    text = re.sub(r'\b10-year-old\b', 'ten year old', text, flags=re.IGNORECASE)
    text = re.sub(r'\b11\b', 'eleven', text)
    text = re.sub(r'\b15\b', 'fifteen', text)
    text = re.sub(r'\b1965\b', 'nineteen sixty-five', text)
    text = re.sub(r'\b1977\b', 'nineteen seventy-seven', text)
    text = re.sub(r'\b1980s\b', 'nineteen eighties', text, flags=re.IGNORECASE)
    text = re.sub(r'\b80s\b', 'eighties', text, flags=re.IGNORECASE)
    text = re.sub(r'\b1983\b', 'nineteen eighty-three', text)
    text = re.sub(r'\b1986\b', 'nineteen eighty-six', text)
    text = re.sub(r'\b1988\b', 'nineteen eighty-eight', text)
    text = re.sub(r'\b1992\b', 'nineteen ninety-two', text)
    text = re.sub(r'\b1993\b', 'nineteen ninety-three', text)

    # Fix Bjork pronunciation
    text = text.replace('Bjork', 'Byerk')
    text = text.replace('bjork', 'byerk')
    text = text.replace('Bjork', 'Byerk')
    text = text.replace('Byork', 'Byerk')

    # Fix other Icelandic names
    text = text.replace('Gudmundsdottir', 'Goodmundsdottir')
    text = text.replace('Gudmundsdottir', 'Goodmundsdottir')

    # Remove em-dashes that might cause pauses
    text = text.replace('—', ', ')

    return text


def contains_strong_word(text: str) -> bool:
    """
    Check if text contains any strong words that need emphasis.

    Args:
        text: Text to check

    Returns:
        True if text contains strong words
    """
    text_lower = text.lower()
    for word in STRONG_WORDS:
        if re.search(r'\b' + word + r'\b', text_lower):
            return True
    return False


def get_intensity_for_sentence(text: str, tension_level: int = 2) -> int:
    """
    Calculate intensity boost percentage for a sentence.

    Args:
        text: Sentence text
        tension_level: Tension level from script metadata (1-5)

    Returns:
        Intensity boost percentage (0, 30, 70, or 100)
    """
    has_strong = contains_strong_word(text)

    # High tension chunks get boost
    if tension_level >= 4:
        return 100 if has_strong else 70
    elif tension_level == 3:
        return 70 if has_strong else 30
    else:
        return 70 if has_strong else 0


def split_into_sentences(text: str) -> list:
    """
    Split text into sentences using regex.
    Handles common sentence endings: . ! ?
    Preserves abbreviations like "Dr." "Mr." "etc."

    Args:
        text: Text to split into sentences

    Returns:
        List of sentence strings
    """
    if not text or not text.strip():
        return []

    # Handle common abbreviations to avoid false splits
    text = text.replace("Dr.", "Dr<DOT>")
    text = text.replace("Mr.", "Mr<DOT>")
    text = text.replace("Mrs.", "Mrs<DOT>")
    text = text.replace("Ms.", "Ms<DOT>")
    text = text.replace("etc.", "etc<DOT>")
    text = text.replace("vs.", "vs<DOT>")
    text = text.replace("i.e.", "i<DOT>e<DOT>")
    text = text.replace("e.g.", "e<DOT>g<DOT>")

    # Split on sentence-ending punctuation followed by space
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    # Restore abbreviations and clean up
    result = []
    for s in sentences:
        s = s.replace("<DOT>", ".")
        s = s.strip()
        if s:
            result.append(s)

    return result
