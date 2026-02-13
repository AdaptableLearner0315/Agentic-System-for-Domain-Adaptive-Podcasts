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
"""

import os
import fal_client
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from agents.base_agent import BaseAgent
from config.image_prompts import CINEMATIC_STYLE, HOOK_PROMPTS, MODULE_PROMPTS

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
    """

    def __init__(self):
        """Initialize the Visual Enhancer Agent."""
        super().__init__(
            name="VisualEnhancer",
            output_category="Visuals Included"
        )

    def generate_image(self, prompt: str, output_path: Path) -> Optional[str]:
        """
        Generate a single image using Fal AI Flux.

        SAFETY: Prompts should avoid direct depictions of real artist faces.

        Args:
            prompt: The image description prompt
            output_path: Full path to save the image

        Returns:
            Path to the generated image, or None if failed
        """
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Enhance prompt with cinematic style
        enhanced_prompt = prompt + CINEMATIC_STYLE

        self.log(f"Generating: {output_path.name}")
        self.log(f"  Prompt: {prompt[:80]}...")

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

    def process(self, enhanced_script: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main processing method - generates all images.

        Args:
            enhanced_script: Optional enhanced script (for future dynamic generation)

        Returns:
            Dictionary with all generated image metadata
        """
        return self.generate_all_images()


if __name__ == "__main__":
    agent = VisualEnhancerAgent()

    # Generate hook images only for testing
    hook_images = agent.generate_hook_images()

    print("\nGenerated images:")
    for img in hook_images:
        print(f"  - {img['id']}: {img['path']}")
