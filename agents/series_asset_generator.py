"""
Series Asset Generator Agent
Author: Sarath

Generates all series-level audio assets for consistent identity:
- Series intro jingle (7 sec)
- Series outro tag (5 sec)
- "Previously on" music bed (25 sec)
- Transition rise audio (5 sec)
- Cliffhanger stings (3-4 sec each, 5 types)
- Emotional motifs (3-4 sec each: tension, wonder, mystery, triumph)

All generation uses StyleDNA for era-appropriate aesthetics.
Assets are generated once per series and reused across all episodes.
"""

import fal_client
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from agents.base_agent import BaseAgent
from config.era_profiles import get_era_profile
from config.cliffhanger_prompts import CLIFFHANGER_TYPES


class SeriesAssetGenerator(BaseAgent):
    """
    Generates audio assets that define a series' sonic identity.

    All assets use the StyleDNA to ensure era-appropriate aesthetics
    that are consistent across all episodes.
    """

    # Asset specifications
    ASSET_SPECS = {
        "identity": {
            "intro_jingle": {
                "duration": 7,
                "description": "Series signature intro, memorable and distinctive",
                "prompt_template": "{era_prefix} series intro jingle, podcast opening, {mood}, memorable melody, professional production, clean ending"
            },
            "outro_tag": {
                "duration": 5,
                "description": "Series closing signature",
                "prompt_template": "{era_prefix} series outro tag, podcast closing, {mood}, satisfying conclusion, fade out ending"
            }
        },
        "transitions": {
            "previously_on_bed": {
                "duration": 25,
                "description": "Lo-fi filtered music bed for recap sections",
                "prompt_template": "{era_prefix} lo-fi filtered music bed, nostalgic processing, vinyl warmth, muted and atmospheric, memory mode, podcast recap underscore"
            },
            "transition_rise": {
                "duration": 5,
                "description": "Transition from recap to main content",
                "prompt_template": "{era_prefix} rising transition, filter opening, energy building, podcast transition, {mood}, anticipation build"
            }
        },
        "motifs": {
            "tension_motif": {
                "duration": 3,
                "description": "Brief tension build for dramatic moments",
                "prompt_template": "dramatic tension motif, suspenseful, {era_prefix}, building dread, podcast stinger, dark undertone"
            },
            "wonder_motif": {
                "duration": 3,
                "description": "Discovery and wonder moment",
                "prompt_template": "wonder and discovery motif, {era_prefix}, magical moment, podcast stinger, curiosity and awe"
            },
            "mystery_motif": {
                "duration": 4,
                "description": "Mystery and intrigue",
                "prompt_template": "mystery motif, {era_prefix}, questioning tone, unresolved, podcast stinger, curious and uncertain"
            },
            "triumph_motif": {
                "duration": 3,
                "description": "Victory and achievement moment",
                "prompt_template": "triumph motif, {era_prefix}, victory moment, podcast stinger, celebratory, {mood}"
            }
        }
    }

    # Cliffhanger stings based on type
    CLIFFHANGER_STING_SPECS = {
        "revelation": {
            "duration": 4,
            "prompt_template": "dramatic sustained orchestral chord, slow fade, mysterious ending, {era_prefix}, cinematic reveal moment, lingering tension"
        },
        "twist": {
            "duration": 3,
            "prompt_template": "dramatic orchestral hit, sudden stop, dead silence, {era_prefix}, shocking reveal, impact moment then nothing"
        },
        "question": {
            "duration": 3,
            "prompt_template": "unresolved piano chord, questioning tone, {era_prefix}, suspended tension, incomplete musical phrase"
        },
        "countdown": {
            "duration": 4,
            "prompt_template": "accelerating clock tick, building orchestral tension, {era_prefix}, urgent countdown, dramatic crescendo then abrupt stop"
        },
        "promise": {
            "duration": 4,
            "prompt_template": "building anticipation music, rising strings, {era_prefix}, crescendo that stops at peak, exciting promise"
        }
    }

    def __init__(self, model: str = None):
        """Initialize the SeriesAssetGenerator."""
        super().__init__(
            name="SeriesAssetGenerator",
            output_category="series",
            model=model
        )

    def generate_series_assets(
        self,
        series_id: str,
        style_dna: Dict[str, Any],
        output_base: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Generate all series audio assets.

        Args:
            series_id: Unique series identifier
            style_dna: StyleDNA from IntentAnalyzer
            output_base: Base output directory (optional)

        Returns:
            SeriesAssets dictionary with all paths
        """
        self.log(f"Generating series assets for {series_id}")

        # Set up output directory
        if output_base:
            assets_dir = Path(output_base) / "assets"
        else:
            assets_dir = self.output_dir / series_id / "assets"

        assets_dir.mkdir(parents=True, exist_ok=True)

        # Get era prefix and mood from style_dna
        era = style_dna.get("era", "modern")
        era_profile = get_era_profile(era)
        music_profile = style_dna.get("music_profile", era_profile.get("music_profile", {}))

        era_prefix = music_profile.get("bgm_prompt_prefix", f"{era} style")
        mood = music_profile.get("mood", "engaging and atmospheric")

        # Build all asset generation tasks
        tasks = []

        # Identity assets
        for asset_name, spec in self.ASSET_SPECS["identity"].items():
            prompt = spec["prompt_template"].format(era_prefix=era_prefix, mood=mood)
            output_path = assets_dir / "identity" / f"{asset_name}.wav"
            tasks.append({
                "name": asset_name,
                "category": "identity",
                "prompt": prompt,
                "duration": spec["duration"],
                "output_path": output_path
            })

        # Transition assets
        for asset_name, spec in self.ASSET_SPECS["transitions"].items():
            prompt = spec["prompt_template"].format(era_prefix=era_prefix, mood=mood)
            output_path = assets_dir / "transitions" / f"{asset_name}.wav"
            tasks.append({
                "name": asset_name,
                "category": "transitions",
                "prompt": prompt,
                "duration": spec["duration"],
                "output_path": output_path
            })

        # Motif assets
        for asset_name, spec in self.ASSET_SPECS["motifs"].items():
            prompt = spec["prompt_template"].format(era_prefix=era_prefix, mood=mood)
            output_path = assets_dir / "motifs" / f"{asset_name}.wav"
            tasks.append({
                "name": asset_name,
                "category": "motifs",
                "prompt": prompt,
                "duration": spec["duration"],
                "output_path": output_path
            })

        # Cliffhanger stings
        for cliffhanger_type, spec in self.CLIFFHANGER_STING_SPECS.items():
            prompt = spec["prompt_template"].format(era_prefix=era_prefix)
            output_path = assets_dir / "stingers" / f"cliffhanger_{cliffhanger_type}.wav"
            tasks.append({
                "name": f"cliffhanger_{cliffhanger_type}",
                "category": "stingers",
                "prompt": prompt,
                "duration": spec["duration"],
                "output_path": output_path
            })

        # Ensure directories exist
        for category in ["identity", "transitions", "motifs", "stingers"]:
            (assets_dir / category).mkdir(parents=True, exist_ok=True)

        # Generate all assets in parallel
        self.log(f"Generating {len(tasks)} audio assets in parallel...")
        results = self._generate_assets_parallel(tasks)

        # Build result structure
        assets = {
            "intro_jingle_path": None,
            "outro_tag_path": None,
            "previously_on_bed_path": None,
            "transition_rise_path": None,
            "cliffhanger_stings": {},
            "motifs": {},
            "generated_at": datetime.utcnow().isoformat()
        }

        for result in results:
            name = result["name"]
            path = result.get("path")
            category = result["category"]

            if path:
                if category == "identity":
                    if name == "intro_jingle":
                        assets["intro_jingle_path"] = str(path)
                    elif name == "outro_tag":
                        assets["outro_tag_path"] = str(path)
                elif category == "transitions":
                    if name == "previously_on_bed":
                        assets["previously_on_bed_path"] = str(path)
                    elif name == "transition_rise":
                        assets["transition_rise_path"] = str(path)
                elif category == "stingers":
                    cliffhanger_type = name.replace("cliffhanger_", "")
                    assets["cliffhanger_stings"][cliffhanger_type] = str(path)
                elif category == "motifs":
                    assets["motifs"][name] = str(path)

        successful = sum(1 for r in results if r.get("path"))
        self.log(f"Generated {successful}/{len(tasks)} assets successfully")

        return assets

    def _generate_assets_parallel(
        self,
        tasks: List[Dict[str, Any]],
        max_workers: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple audio assets in parallel.

        Args:
            tasks: List of task dicts with name, prompt, duration, output_path
            max_workers: Maximum parallel workers

        Returns:
            List of results with name and path (or error)
        """
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._generate_single_asset,
                    task["prompt"],
                    task["duration"],
                    task["output_path"]
                ): task
                for task in tasks
            }

            for future in as_completed(futures):
                task = futures[future]
                try:
                    path = future.result()
                    results.append({
                        "name": task["name"],
                        "category": task["category"],
                        "path": path,
                        "success": path is not None
                    })
                except Exception as e:
                    self.log(f"Failed to generate {task['name']}: {e}", level="error")
                    results.append({
                        "name": task["name"],
                        "category": task["category"],
                        "path": None,
                        "success": False,
                        "error": str(e)
                    })

        return results

    def _generate_single_asset(
        self,
        prompt: str,
        duration: int,
        output_path: Path
    ) -> Optional[str]:
        """
        Generate a single audio asset using Fal AI.

        Args:
            prompt: Generation prompt
            duration: Duration in seconds
            output_path: Path to save output

        Returns:
            Path string if successful, None otherwise
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            result = fal_client.subscribe(
                "fal-ai/stable-audio",
                arguments={
                    "prompt": prompt,
                    "seconds_total": min(duration, 47),  # Fal AI max is 47s
                    "steps": 100
                },
                with_logs=False
            )

            audio_url = result.get("audio_file", {}).get("url")
            if audio_url:
                response = requests.get(audio_url, timeout=30)
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return str(output_path)

            return None

        except Exception as e:
            self.log(f"Fal AI error: {e}", level="error")
            return None

    def generate_single_sting(
        self,
        cliffhanger_type: str,
        style_dna: Dict[str, Any],
        output_path: Path
    ) -> Optional[str]:
        """
        Generate a single cliffhanger sting.

        Useful for regenerating a specific sting without full asset generation.

        Args:
            cliffhanger_type: Type of cliffhanger
            style_dna: StyleDNA for era-appropriate generation
            output_path: Where to save the sting

        Returns:
            Path to generated audio or None
        """
        if cliffhanger_type not in self.CLIFFHANGER_STING_SPECS:
            self.log(f"Unknown cliffhanger type: {cliffhanger_type}", level="error")
            return None

        spec = self.CLIFFHANGER_STING_SPECS[cliffhanger_type]
        era = style_dna.get("era", "modern")
        era_profile = get_era_profile(era)
        music_profile = style_dna.get("music_profile", era_profile.get("music_profile", {}))
        era_prefix = music_profile.get("bgm_prompt_prefix", f"{era} style")

        prompt = spec["prompt_template"].format(era_prefix=era_prefix)

        return self._generate_single_asset(prompt, spec["duration"], output_path)

    def process(self, *args, **kwargs) -> Any:
        """Main entry point - alias for generate_series_assets()."""
        return self.generate_series_assets(*args, **kwargs)


# Convenience function
def generate_series_assets(
    series_id: str,
    style_dna: Dict[str, Any],
    output_base: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Quick function to generate series assets.

    Args:
        series_id: Unique series identifier
        style_dna: StyleDNA from IntentAnalyzer
        output_base: Base output directory

    Returns:
        SeriesAssets dictionary with all paths
    """
    generator = SeriesAssetGenerator()
    return generator.generate_series_assets(series_id, style_dna, output_base)
