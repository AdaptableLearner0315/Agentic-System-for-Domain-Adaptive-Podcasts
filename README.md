# Podcast Enhancement System

**Author:** Sarath

> Creating Scalable Domain Adaptive Reliable podcasts

## Overview

An agentic system that transforms raw audio into immersive, emotionally engaging podcast experiences with AI-generated narration, background music, and visuals.

## Architecture

```
                    ┌─────────────────────────────────┐
                    │        Director Agent           │
                    │   (Orchestrator + Reviewer)     │
                    └───────────────┬─────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│ Script Designer │     │   Audio Designer    │     │ Visual Enhancer │
│     Agent       │     │      Agent          │     │     Agent       │
├─────────────────┤     ├─────────────────────┤     ├─────────────────┤
│ - Enhancement   │     │ - TTS Narrator      │     │ - Image Gen     │
│ - Emotion Arc   │     │ - Voice Style Eng   │     │ - Inflection    │
│ - Module Split  │     │ - BGM Generator     │     │   Analysis      │
└─────────────────┘     │ - Audio Mixer       │     └─────────────────┘
                        └─────────────────────┘
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FAL_KEY=your-fal-key
export ANTHROPIC_API_KEY=your-anthropic-key

# Run full pipeline
python run_pipeline.py full --input Input/transcript.txt
```

## Commands

| Command | Description |
|---------|-------------|
| `python run_pipeline.py enhance` | Enhance transcript with emotional arc |
| `python run_pipeline.py audio` | Generate TTS and background music |
| `python run_pipeline.py visual` | Generate narrative-driven images |
| `python run_pipeline.py full` | Run complete pipeline |

## Tech Stack

- **LLM:** Gemini 3 Pro (Google)
- **TTS:** MiniMax Speech-01-HD (Fal AI)
- **BGM:** Stable Audio (Fal AI)
- **Images:** Flux (Fal AI)
- **Video:** FFmpeg

## License

MIT
