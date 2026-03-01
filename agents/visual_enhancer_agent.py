"""
Visual Enhancer Agent
Author: Sarath

Generates cinematic images using Fal AI Flux model for podcast visuals.

SAFETY CONSTRAINT: No artist faces or direct depictions of real people.
All image prompts use settings, objects, landscapes, and atmospheric imagery.

Features:
- Narrative-driven image generation
- Module-specific visual themes
- Cinematic photography style
- Emotion-aligned visual styling (color palette, lighting, mood, composition)
"""

import os
import fal_client
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from agents.base_agent import BaseAgent
from config.image_prompts import CINEMATIC_STYLE, HOOK_PROMPTS, MODULE_PROMPTS
from config.emotion_visual_mapping import (
    get_emotion_visual_style,
    build_emotion_prompt_suffix,
    EMOTION_VISUAL_STYLE
)

load_dotenv()


class VisualEnhancerAgent(BaseAgent):
    """
    Agent for generating narrative-driven images for podcast videos.

    SAFETY: All image generation avoids direct depictions of real artist faces.
    Uses settings, objects, landscapes, and atmospheric imagery instead.

    Features:
    - Hook image generation with emotional themes
    - Module-specific visual narratives
    - Cinematic photography style enhancement
    - Emotion-aligned visual styling (color, lighting, mood, composition)
    """

    def __init__(self, emotion_aligned: bool = True):
        """
        Initialize the Visual Enhancer Agent.

        Args:
            emotion_aligned: Whether to include emotion-based visual styling in prompts
        """
        super().__init__(
            name="VisualEnhancer",
            output_category="Visuals Included"
        )
        self.emotion_aligned = emotion_aligned

    def generate_emotion_aligned_prompt(
        self,
        narrative_cue: str,
        emotion: str
    ) -> str:
        """
        Create image prompt that combines narrative content with emotional visual style.

        Args:
            narrative_cue: The narrative description of the image
            emotion: Emotion to align visual style with

        Returns:
            Enhanced prompt with emotion-based visual styling
        """
        if not self.emotion_aligned or not emotion or emotion.lower() == "neutral":
            return narrative_cue + CINEMATIC_STYLE

        # Get emotion visual style
        visual_style = get_emotion_visual_style(emotion)

        # Build enhanced prompt
        prompt_parts = [
            narrative_cue,
            f"{visual_style['mood']} atmosphere",
            f"{visual_style['color_palette']}",
            f"{visual_style['lighting']}",
            f"{visual_style['composition']}",
            CINEMATIC_STYLE.strip(", ")
        ]

        enhanced_prompt = ", ".join(prompt_parts)

        self.log(f"  Emotion-aligned prompt ({emotion}): {len(enhanced_prompt)} chars")

        return enhanced_prompt

    def set_emotion_aligned(self, enabled: bool):
        """Enable or disable emotion-aligned visual styling."""
        self.emotion_aligned = enabled
        self.log(f"Emotion alignment {'enabled' if enabled else 'disabled'}")

    def generate_image(
        self,
        prompt: str,
        output_path: Path,
        emotion: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a single image using Fal AI Flux.

        SAFETY: Prompts should avoid direct depictions of real artist faces.

        Args:
            prompt: The image description prompt
            output_path: Full path to save the image
            emotion: Optional emotion for visual style alignment

        Returns:
            Path to the generated image, or None if failed
        """
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Enhance prompt with cinematic style (and optionally emotion)
        if emotion and self.emotion_aligned:
            enhanced_prompt = self.generate_emotion_aligned_prompt(prompt, emotion)
        else:
            enhanced_prompt = prompt + CINEMATIC_STYLE

        self.log(f"Generating: {output_path.name}")
        self.log(f"  Prompt: {prompt[:80]}...")
        if emotion:
            self.log(f"  Emotion: {emotion}")

        try:
            result = fal_client.subscribe(
                "fal-ai/flux/dev",
                arguments={
                    "prompt": enhanced_prompt,
                    "image_size": "landscape_16_9",
                    "num_images": 1,
                    "enable_safety_checker": False
                },
                with_logs=False
            )

            # Get the image URL
            images = result.get("images", [])
            if images and len(images) > 0:
                image_url = images[0].get("url")
                if image_url:
                    # Download and save
                    response = requests.get(image_url)
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    self.log(f"  Saved: {output_path}")
                    return str(output_path)

            self.log("  Error: No image generated", level="error")
            return None

        except Exception as e:
            self.log(f"  Error generating image: {e}", level="error")
            return None

    def generate_hook_images(self) -> List[Dict[str, Any]]:
        """
        Generate images for the hook section.

        Images are designed for 20-40s duration each with emotional themes.

        Returns:
            List of generated image metadata
        """
        hook_dir = self.output_dir / "hook"
        hook_dir.mkdir(parents=True, exist_ok=True)

        print("=" * 60)
        print(f"GENERATING HOOK IMAGES ({len(HOOK_PROMPTS)} images, ~20-40s each)")
        print("=" * 60)

        generated = []
        for i, img_config in enumerate(HOOK_PROMPTS, 1):
            print(f"\n[{i}/{len(HOOK_PROMPTS)}] {img_config['id']} "
                  f"(Sentences: {img_config['sentences']}, {img_config.get('duration_hint', '')})")

            output_path = hook_dir / f"{img_config['id']}.png"
            result = self.generate_image(img_config['prompt'], output_path)

            if result:
                generated.append({
                    "id": img_config['id'],
                    "path": result,
                    "prompt": img_config['prompt'],
                    "sentences": img_config['sentences']
                })

        print(f"\n" + "=" * 60)
        print(f"HOOK IMAGES COMPLETE: {len(generated)}/{len(HOOK_PROMPTS)} generated")
        print(f"Location: {hook_dir}")
        print("=" * 60)

        return generated

    def generate_module_images(self, module_id: int) -> List[Dict[str, Any]]:
        """
        Generate images for a specific module.

        SAFETY: All module prompts avoid direct depictions of real artist faces.

        Args:
            module_id: Module ID (1-4)

        Returns:
            List of generated image metadata
        """
        module_dir = self.output_dir / f"module_{module_id}"
        module_dir.mkdir(parents=True, exist_ok=True)

        prompts = MODULE_PROMPTS.get(module_id, [])

        print("=" * 60)
        print(f"GENERATING MODULE {module_id} IMAGES ({len(prompts)} images)")
        print("=" * 60)

        generated = []
        for i, img_config in enumerate(prompts, 1):
            print(f"\n[{i}/{len(prompts)}] {img_config['id']}")

            output_path = module_dir / f"{img_config['id']}.png"
            result = self.generate_image(img_config['prompt'], output_path)

            if result:
                generated.append({
                    "id": img_config['id'],
                    "path": result,
                    "prompt": img_config['prompt']
                })

        print(f"\n" + "=" * 60)
        print(f"MODULE {module_id} IMAGES COMPLETE: {len(generated)}/{len(prompts)} generated")
        print(f"Location: {module_dir}")
        print("=" * 60)

        return generated

    def generate_all_images(self) -> Dict[str, Any]:
        """
        Generate all images for the podcast (hook + all modules).

        Returns:
            Dictionary with all generated image metadata
        """
        self.log("Starting full image generation...")

        results = {
            "hook": self.generate_hook_images(),
            "modules": {}
        }

        for module_id in range(1, 5):
            results["modules"][module_id] = self.generate_module_images(module_id)

        total_images = len(results["hook"]) + sum(
            len(images) for images in results["modules"].values()
        )
        self.log(f"Total images generated: {total_images}")

        return results

    def generate_images_from_script(
        self,
        enhanced_script: Dict[str, Any],
        images_per_module: int = 4
    ) -> Dict[str, Any]:
        """
        Generate images dynamically from enhanced script with emotion alignment.

        This method generates images based on the actual script content and emotions,
        rather than using predefined prompts.

        Args:
            enhanced_script: Enhanced script with modules and emotions
            images_per_module: Number of images per module

        Returns:
            Dictionary with generated image metadata
        """
        results = {
            "hook": [],
            "modules": {}
        }

        # Generate hook images
        hook = enhanced_script.get("hook", {})
        if hook.get("text"):
            hook_emotion = hook.get("emotion", "intrigue")
            hook_visual_cues = hook.get("visual_cues", [])

            print("=" * 60)
            print(f"GENERATING HOOK IMAGES (emotion: {hook_emotion})")
            print("=" * 60)

            hook_dir = self.output_dir / "hook"
            hook_dir.mkdir(parents=True, exist_ok=True)

            # Use visual cues if available, otherwise use default prompts
            if hook_visual_cues:
                for i, cue in enumerate(hook_visual_cues[:2], 1):
                    output_path = hook_dir / f"hook_emotion_img_{i}.png"
                    result = self.generate_image(cue, output_path, emotion=hook_emotion)
                    if result:
                        results["hook"].append({
                            "id": f"hook_emotion_img_{i}",
                            "path": result,
                            "prompt": cue,
                            "emotion": hook_emotion
                        })
            else:
                # Fall back to default hook prompts
                results["hook"] = self.generate_hook_images()

        # Generate module images with emotion alignment
        modules = enhanced_script.get("modules", [])
        for module in modules:
            module_id = module.get("id", 1)
            module_emotion_arc = module.get("emotion_arc", "neutral")
            chunks = module.get("chunks", [])

            print(f"\n" + "=" * 60)
            print(f"GENERATING MODULE {module_id} IMAGES (arc: {module_emotion_arc})")
            print("=" * 60)

            module_dir = self.output_dir / f"module_{module_id}"
            module_dir.mkdir(parents=True, exist_ok=True)

            module_images = []
            img_count = 0

            for chunk in chunks:
                chunk_emotion = chunk.get("emotion", "neutral")
                visual_cues = chunk.get("visual_cues", [])

                for cue in visual_cues:
                    if img_count >= images_per_module:
                        break

                    img_count += 1
                    output_path = module_dir / f"module_{module_id}_emotion_img_{img_count}.png"

                    result = self.generate_image(cue, output_path, emotion=chunk_emotion)
                    if result:
                        module_images.append({
                            "id": f"module_{module_id}_emotion_img_{img_count}",
                            "path": result,
                            "prompt": cue,
                            "emotion": chunk_emotion
                        })

                if img_count >= images_per_module:
                    break

            # If not enough images from visual cues, use default prompts
            if img_count < images_per_module and module_id in MODULE_PROMPTS:
                remaining = images_per_module - img_count
                default_prompts = MODULE_PROMPTS[module_id][:remaining]
                for img_config in default_prompts:
                    output_path = module_dir / f"{img_config['id']}.png"
                    # Get dominant emotion from module
                    dominant_emotion = chunks[0].get("emotion", "neutral") if chunks else "neutral"
                    result = self.generate_image(
                        img_config['prompt'],
                        output_path,
                        emotion=dominant_emotion
                    )
                    if result:
                        module_images.append({
                            "id": img_config['id'],
                            "path": result,
                            "prompt": img_config['prompt'],
                            "emotion": dominant_emotion
                        })

            results["modules"][module_id] = module_images

        total_images = len(results["hook"]) + sum(
            len(images) for images in results["modules"].values()
        )
        self.log(f"Total emotion-aligned images generated: {total_images}")

        return results

    def process(self, enhanced_script: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main processing method - generates all images.

        Args:
            enhanced_script: Optional enhanced script for dynamic emotion-aligned generation

        Returns:
            Dictionary with all generated image metadata
        """
        if enhanced_script and self.emotion_aligned:
            # Use script-based generation with emotion alignment
            return self.generate_images_from_script(enhanced_script)
        else:
            # Use default prompts
            return self.generate_all_images()


if __name__ == "__main__":
    agent = VisualEnhancerAgent(emotion_aligned=True)

    # Generate hook images only for testing
    hook_images = agent.generate_hook_images()

    print("\nGenerated images:")
    for img in hook_images:
        print(f"  - {img['id']}: {img['path']}")
