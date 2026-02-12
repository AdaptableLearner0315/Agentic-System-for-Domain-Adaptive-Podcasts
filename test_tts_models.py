"""Test available TTS models on Fal.ai"""
import fal_client
from dotenv import load_dotenv
load_dotenv()

# Test available TTS models on Fal.ai
models = [
    ('fal-ai/f5-tts', {'gen_text': 'Test', 'ref_audio_url': 'https://github.com/SWivid/F5-TTS/raw/refs/heads/main/src/f5_tts/infer/examples/basic/basic_ref_en.wav'}),
    ('fal-ai/metavoice-v1', {'text': 'Test', 'guidance_scale': 3.0}),
    ('fal-ai/parler-tts', {'prompt': 'Test', 'description': 'A female narrator speaks clearly'}),
    ('fal-ai/bark', {'text': 'Test'}),
    ('fal-ai/tortoise-tts', {'text': 'Test'}),
    ('fal-ai/eleven-labs', {'text': 'Test'}),
]

print("Testing available TTS models on Fal.ai:")
print("=" * 60)

for model_name, args in models:
    print(f"\n{model_name}:")
    try:
        # Just submit to check if model exists (don't wait for result)
        handle = fal_client.submit(model_name, arguments=args)
        print(f"  ✓ Available - Request ID: {handle.request_id[:20]}...")
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            print(f"  ✗ Not available")
        else:
            print(f"  ? Error: {error_msg[:100]}")
