"""
Image Asset Manager
Author: Sarath

Manages pre-generated image library for fast visual selection.
Uses smart matching to select relevant images from library.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
import random


class ImageAssetManager:
    """
    Manages categorized image library for fast visual assembly.

    Features:
    - Categorized image library
    - Smart keyword matching
    - Visual cue to image mapping
    - Fallback image selection
    """

    # Image categories with keywords
    CATEGORIES = {
        "landscape": {
            "keywords": ["iceland", "mountain", "ocean", "forest", "sky", "horizon", "nature", "outdoor"],
            "description": "Natural landscapes and outdoor scenes",
        },
        "abstract": {
            "keywords": ["emotion", "concept", "texture", "pattern", "color", "light", "shadow", "dream"],
            "description": "Abstract visuals and emotional representations",
        },
        "space": {
            "keywords": ["studio", "stage", "room", "building", "interior", "architecture", "club", "venue"],
            "description": "Indoor spaces and architectural settings",
        },
        "object": {
            "keywords": ["instrument", "technology", "art", "music", "vinyl", "microphone", "equipment"],
            "description": "Objects and props",
        },
        "atmosphere": {
            "keywords": ["fog", "mist", "particles", "rain", "snow", "aurora", "stars", "glow"],
            "description": "Atmospheric effects and moods",
        },
    }

    # Cinematic style suffix for generation
    CINEMATIC_STYLE = ", cinematic photography, documentary style, photorealistic, film grain, 35mm film aesthetic, professional lighting, high quality"

    def __init__(self, asset_dir: Optional[Path] = None):
        """
        Initialize the Image Asset Manager.

        Args:
            asset_dir: Directory for image assets
        """
        if asset_dir:
            self.asset_dir = Path(asset_dir)
        else:
            self.asset_dir = Path(__file__).parent / "images"

        self.asset_dir.mkdir(parents=True, exist_ok=True)

        # Create category subdirectories
        for category in self.CATEGORIES:
            (self.asset_dir / category).mkdir(exist_ok=True)

        # Image catalog
        self._image_catalog: Dict[str, List[Dict[str, Any]]] = {}
        self._load_catalog()

    def _load_catalog(self):
        """Load image catalog from disk."""
        catalog_file = self.asset_dir / "catalog.json"
        if catalog_file.exists():
            try:
                with open(catalog_file, 'r') as f:
                    self._image_catalog = json.load(f)
            except Exception:
                self._image_catalog = {cat: [] for cat in self.CATEGORIES}
        else:
            self._image_catalog = {cat: [] for cat in self.CATEGORIES}

    def _save_catalog(self):
        """Save image catalog to disk."""
        catalog_file = self.asset_dir / "catalog.json"
        with open(catalog_file, 'w') as f:
            json.dump(self._image_catalog, f, indent=2)

    def _classify_cue(self, visual_cue: str) -> str:
        """
        Classify a visual cue into a category.

        Args:
            visual_cue: Visual cue text

        Returns:
            Best matching category
        """
        cue_lower = visual_cue.lower()
        scores = {}

        for category, config in self.CATEGORIES.items():
            score = sum(1 for kw in config["keywords"] if kw in cue_lower)
            scores[category] = score

        # Return category with highest score, or 'abstract' as fallback
        best = max(scores.items(), key=lambda x: x[1])
        return best[0] if best[1] > 0 else "abstract"

    def add_image(
        self,
        category: str,
        image_path: str,
        keywords: List[str],
        prompt: Optional[str] = None
    ):
        """
        Add an image to the catalog.

        Args:
            category: Image category
            image_path: Path to image file
            keywords: Keywords describing the image
            prompt: Original generation prompt
        """
        if category not in self._image_catalog:
            self._image_catalog[category] = []

        self._image_catalog[category].append({
            "path": str(image_path),
            "keywords": keywords,
            "prompt": prompt,
        })
        self._save_catalog()

    def find_matching_images(
        self,
        visual_cue: str,
        count: int = 1
    ) -> List[str]:
        """
        Find images matching a visual cue.

        Args:
            visual_cue: Visual cue to match
            count: Number of images to return

        Returns:
            List of image paths
        """
        category = self._classify_cue(visual_cue)
        cue_words = set(visual_cue.lower().split())

        # Get all images in category
        images = self._image_catalog.get(category, [])

        # Score images by keyword overlap
        scored = []
        for img in images:
            img_words = set(kw.lower() for kw in img.get("keywords", []))
            score = len(cue_words & img_words)
            scored.append((score, img["path"]))

        # Sort by score and return top matches
        scored.sort(reverse=True, key=lambda x: x[0])

        paths = [path for _, path in scored[:count] if Path(path).exists()]
        return paths

    def select_images(
        self,
        visual_cues: List[str],
        count: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Select images for a list of visual cues.

        Args:
            visual_cues: List of visual cue descriptions
            count: Total images to select

        Returns:
            List of selected image metadata
        """
        selected = []
        used_paths = set()

        # Try to find matches for each cue
        for cue in visual_cues[:count]:
            matches = self.find_matching_images(cue, count=3)

            # Select first unused match
            for path in matches:
                if path not in used_paths:
                    selected.append({
                        "path": path,
                        "cue": cue,
                        "from_library": True,
                    })
                    used_paths.add(path)
                    break

        return selected

    def smart_select(
        self,
        visual_cues: List[str],
        count: int = 4,
        generate_missing: bool = True,
        image_func = None
    ) -> List[Dict[str, Any]]:
        """
        Smart selection combining library and generation.

        Args:
            visual_cues: Visual cues from script
            count: Number of images needed
            generate_missing: Whether to generate if not in library
            image_func: Image generation function (prompt, filename) -> path

        Returns:
            List of image metadata
        """
        selected = []
        used_paths = set()

        for i, cue in enumerate(visual_cues[:count]):
            # Try library first
            matches = self.find_matching_images(cue, count=2)
            found = False

            for path in matches:
                if path not in used_paths:
                    selected.append({
                        "path": path,
                        "cue": cue,
                        "from_library": True,
                        "index": i,
                    })
                    used_paths.add(path)
                    found = True
                    break

            # Generate if not found and function provided
            if not found and generate_missing and image_func:
                full_prompt = cue + self.CINEMATIC_STYLE
                filename = f"generated_{i+1}"
                path = image_func(full_prompt, filename)

                if path:
                    selected.append({
                        "path": path,
                        "cue": cue,
                        "from_library": False,
                        "index": i,
                    })
                    # Add to catalog for future use
                    category = self._classify_cue(cue)
                    keywords = cue.lower().split()[:5]
                    self.add_image(category, path, keywords, full_prompt)

        return selected

    def get_library_stats(self) -> Dict[str, int]:
        """Get count of images per category."""
        return {cat: len(imgs) for cat, imgs in self._image_catalog.items()}

    def pregenerate_library(
        self,
        image_func,
        images_per_category: int = 10
    ):
        """
        Pre-generate images for each category.

        Args:
            image_func: Image generation function (prompt, filename) -> path
            images_per_category: Number of images per category
        """
        print("[ImageAssetManager] Pre-generating image library...")

        # Sample prompts for each category
        SAMPLE_PROMPTS = {
            "landscape": [
                "Dramatic Icelandic landscape with glaciers and volcanic terrain",
                "Misty mountain peaks at sunrise with golden light",
                "Calm ocean horizon at twilight with stars emerging",
                "Dense forest path with dappled sunlight",
                "Aurora borealis over snow-covered landscape",
            ],
            "abstract": [
                "Abstract visualization of wonder and curiosity, swirling colors",
                "Emotional representation of triumph, golden light rays",
                "Textured abstract of tension and anticipation, dark contrasts",
                "Dreamlike abstract of reflection, soft gradients",
                "Conceptual image of transformation, metamorphosis",
            ],
            "space": [
                "Professional recording studio with warm lighting",
                "Intimate concert venue stage with dramatic spotlight",
                "Vintage radio station interior with equipment",
                "Modern podcast studio with acoustic panels",
                "Historic theater stage from audience perspective",
            ],
            "object": [
                "Vintage vinyl record player with records scattered",
                "Professional microphone in dim studio lighting",
                "Musical instruments arranged artistically",
                "Retro audio equipment with glowing tubes",
                "Artist's workspace with creative tools",
            ],
            "atmosphere": [
                "Morning fog rolling through valley",
                "Particle-filled spotlight beam in darkness",
                "Gentle rain on window with bokeh lights",
                "Swirling aurora patterns in night sky",
                "Dust motes in golden sunbeam",
            ],
        }

        for category, prompts in SAMPLE_PROMPTS.items():
            current_count = len(self._image_catalog.get(category, []))

            for i, prompt in enumerate(prompts[:images_per_category - current_count]):
                filename = f"{category}_{current_count + i + 1}"
                full_prompt = prompt + self.CINEMATIC_STYLE

                print(f"  Generating: {filename}")
                path = image_func(full_prompt, filename)

                if path:
                    keywords = prompt.lower().split()[:5]
                    self.add_image(category, path, keywords, full_prompt)

        stats = self.get_library_stats()
        total = sum(stats.values())
        print(f"[ImageAssetManager] Library ready: {total} images across {len(stats)} categories")


__all__ = ['ImageAssetManager']
