"""Regenerate BGM for specific modules with new emotions."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agents.music_generator import MusicGenerator

def main():
    generator = MusicGenerator()

    # Regenerate module 3 with "liberation" emotion
    print("Regenerating BGM for Module 3 (liberation)...")
    path3 = generator.generate_bgm("liberation", "module_3_bgm", duration=45)
    print(f"Module 3 BGM: {path3}")

    # Regenerate module 4 with "mastery" emotion
    print("\nRegenerating BGM for Module 4 (mastery)...")
    path4 = generator.generate_bgm("mastery", "module_4_bgm", duration=45)
    print(f"Module 4 BGM: {path4}")

    print("\nBGM regeneration complete!")

if __name__ == "__main__":
    main()
