"""
Image Generator Agent

Generates cinematic images using Fal AI Flux model for podcast visuals.
"""

import os
import fal_client
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base style suffix for all prompts
CINEMATIC_STYLE = ", cinematic photography, documentary style, photorealistic, film grain, 35mm film aesthetic, professional lighting, high quality"


class ImageGenerator:
    def __init__(self):
        self.output_dir = Path(__file__).parent.parent / "Output" / "Visuals Included"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_image(self, prompt: str, output_path: Path) -> str:
        """
        Generate a single image using Fal AI Flux.

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

        print(f"  Generating: {output_path.name}")
        print(f"    Prompt: {prompt[:80]}...")

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
                    print(f"    Saved: {output_path}")
                    return str(output_path)

            print(f"    Error: No image generated")
            return None

        except Exception as e:
            print(f"    Error generating image: {e}")
            return None

    def generate_hook_images(self) -> list:
        """Generate images for the hook section (20-40s per image, emotion-driven)."""
        hook_dir = self.output_dir / "hook"
        hook_dir.mkdir(parents=True, exist_ok=True)

        print("=" * 60)
        print("GENERATING HOOK IMAGES (2 images, ~20-40s each)")
        print("=" * 60)

        # Hook is ~46 seconds, so 2 images:
        # - Image 1: The iconic performance moment (sentences 1-4, ~30s)
        # - Image 2: The journey pivot (sentences 5-6, ~16s)
        hook_prompts = [
            {
                "id": "hook_img_1",
                "prompt": "10-year-old Icelandic girl performing on school stage, piano visible, spotlight illuminating her face as she sings with intense otherworldly expression, wooden auditorium filled with captivated audience, Reykjavik 1975, historic moment captured",
                "sentences": "1-4",
                "duration_hint": "~30s"
            },
            {
                "id": "hook_img_2",
                "prompt": "Epic wide shot of volcanic Iceland landscape with dramatic sky, small figure of young artist silhouetted against the vastness, symbolizing the beginning of an extraordinary journey from isolation to global icon",
                "sentences": "5-6",
                "duration_hint": "~16s"
            }
        ]

        generated = []
        for i, img_config in enumerate(hook_prompts, 1):
            print(f"\n[{i}/{len(hook_prompts)}] {img_config['id']} (Sentences: {img_config['sentences']}, {img_config.get('duration_hint', '')})")

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
        print(f"HOOK IMAGES COMPLETE: {len(generated)}/{len(hook_prompts)} generated")
        print(f"Location: {hook_dir}")
        print("=" * 60)

        return generated

    def generate_module_images(self, module_id: int) -> list:
        """Generate images for a specific module."""
        module_dir = self.output_dir / f"module_{module_id}"
        module_dir.mkdir(parents=True, exist_ok=True)

        # Module-specific prompts
        module_prompts = {
            1: [
                {"id": "module_1_img_1", "prompt": "Misty volcanic landscape Iceland, geothermal steam rising from ground, dramatic moody overcast sky, wide cinematic shot"},
                {"id": "module_1_img_2", "prompt": "Bohemian commune buildings 1960s Iceland, small artistic community houses, warm nostalgic color tones, hippie era"},
                {"id": "module_1_img_3", "prompt": "Communal creative space filled with musical instruments, artists working together, warm golden hour lighting through windows"},
                {"id": "module_1_img_4", "prompt": "Small child hands on piano keys, serious young girl practicing classical music, intimate documentary close-up shot"},
                {"id": "module_1_img_5", "prompt": "Vinyl records spinning on vintage turntable, Jimi Hendrix album cover visible, 1970s stereo equipment, warm lighting"},
                {"id": "module_1_img_6", "prompt": "Aurora borealis northern lights dancing over Reykjavik, geothermal pools steaming in foreground, magical night sky"},
                {"id": "module_1_img_7", "prompt": "Young serious-faced Icelandic girl gazing at dramatic volcanic landscape, contemplative mood, wind in hair"},
            ],
            2: [
                {"id": "module_2_img_1", "prompt": "School auditorium Iceland 1975, wooden stage with piano, vintage recording equipment set up, anticipation atmosphere"},
                {"id": "module_2_img_2", "prompt": "11-year-old girl at professional studio microphone, recording studio 1977, concentrated expression, historic moment"},
                {"id": "module_2_img_3", "prompt": "Debut album cover design session in progress, record label office 1977, creative process, vintage aesthetic"},
                {"id": "module_2_img_4", "prompt": "Teenage girl in 1980s Iceland, new wave fashion aesthetic, local celebrity vibe, restless creative energy"},
                {"id": "module_2_img_5", "prompt": "1980s Iceland Reykjavik street scene, emerging punk and new wave culture, youth gathering, rebellion brewing"},
            ],
            3: [
                {"id": "module_3_img_1", "prompt": "Icelandic punk rock scene 1980s, small smoky underground club interior, raw DIY energy, dim lighting"},
                {"id": "module_3_img_2", "prompt": "Grainy documentary footage aesthetic, wild energetic performance on tiny stage, feral intensity, punk rock"},
                {"id": "module_3_img_3", "prompt": "Young female punk singer commanding small stage, wild spiky hair and dramatic makeup, defying boundaries"},
                {"id": "module_3_img_4", "prompt": "Political gathering with experimental avant-garde music performance, anarcho-punk collective, KUKL era Iceland"},
                {"id": "module_3_img_5", "prompt": "Artistic wedding photo 1986 Iceland, young musician couple, bohemian community celebration, hopeful"},
                {"id": "module_3_img_6", "prompt": "The Sugarcubes band formation group photo, Icelandic musicians, breaking international barriers, hopeful new chapter"},
            ],
            4: [
                {"id": "module_4_img_1", "prompt": "Top of the Pops TV studio performance 1988, international spotlight, colorful 80s TV set, global breakthrough moment"},
                {"id": "module_4_img_2", "prompt": "Music album charts showing international success, press coverage collage, million copies celebration, 1980s media"},
                {"id": "module_4_img_3", "prompt": "Band tension in recording studio, creative differences visible through body language, isolated artist, melancholic mood"},
                {"id": "module_4_img_4", "prompt": "Solo female artist in modern 1990s recording studio, mixing boards and electronic equipment, orchestral meets electronic"},
                {"id": "module_4_img_5", "prompt": "Evolution montage showing iconic artistic looks through decades, avant-garde fashion, bold reinvention"},
                {"id": "module_4_img_6", "prompt": "Iceland volcanic landscape with ethereal artistic overlay, full circle journey, revolutionary artist legacy, epic conclusion"},
            ]
        }

        prompts = module_prompts.get(module_id, [])

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


if __name__ == "__main__":
    generator = ImageGenerator()

    # Generate hook images
    hook_images = generator.generate_hook_images()

    print("\nGenerated images:")
    for img in hook_images:
        print(f"  - {img['id']}: {img['path']}")
