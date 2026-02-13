import fal_client
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Path to the audio file
AUDIO_FILE = "/Users/sarathchandra/Desktop/Interview Submissions/Nell/Input/Nell Take Home.mp3"

def transcribe_audio():
    # Upload the audio file to fal storage
    print("Uploading audio file to Fal AI...")
    audio_url = fal_client.upload_file(AUDIO_FILE)
    print(f"File uploaded: {audio_url}")

    # Use Fal AI's Whisper model for transcription
    print("\nTranscribing audio (this may take a moment)...")
    result = fal_client.subscribe(
        "fal-ai/whisper",
        arguments={
            "audio_url": audio_url,
            "task": "transcribe",
            "chunk_level": "segment",
            "version": "3"  # Use Whisper large-v3
        },
        with_logs=True
    )

    return result

if __name__ == "__main__":
    # Check for API key
    if not os.environ.get("FAL_KEY"):
        print("Error: FAL_KEY environment variable is not set.")
        print("Please set your Fal AI API key:")
        print("  export FAL_KEY='your-api-key-here'")
        print("\nYou can get an API key from: https://fal.ai/dashboard/keys")
        exit(1)

    result = transcribe_audio()

    # Print the full transcription
    print("\n" + "="*60)
    print("TRANSCRIPTION:")
    print("="*60)
    print(result.get("text", "No text found"))

    # Save results to file
    output_path = "/Users/sarathchandra/Desktop/Interview Submissions/Nell/transcript_fal.txt"
    with open(output_path, "w") as f:
        f.write(result.get("text", ""))
    print(f"\nTranscript saved to: {output_path}")

    # Save full JSON result for reference
    json_path = "/Users/sarathchandra/Desktop/Interview Submissions/Nell/transcript_fal_full.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Full result saved to: {json_path}")
