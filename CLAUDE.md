# Podcast Enhancement System - CLAUDE.md

**Author: Sarath**

This document provides context for Claude Code to operate effectively in this repository.

## Project Overview

An agentic podcast enhancement system that transforms raw audio into an engaging, multi-sensory video experience. The system uses AI to:
1. Transcribe audio to text
2. Restructure the script for maximum engagement (emotional arcs, hooks)
3. Generate TTS narration with module-specific voice styles
4. Generate AI background music using 9-segment daisy-chain conditioning
5. Mix audio with VAD-based ducking and emotionally connective pacing
6. Generate narrative-driven images using Fal AI Flux
7. Assemble final video with images synced to audio

**Current state:** Full audio + visual pipeline is functional with advanced BGM generation. Final output is a video podcast with narrative-driven imagery and seamlessly evolving background music.

## Architecture

```
                              run_pipeline.py
                           (Unified Entry Point)
                                    |
         ┌──────────┬──────────┬────┴────┬──────────┬──────────┐
         |          |          |         |          |          |
      enhance    audio      visual     full      preview     bgm
         |          |          |         |          |          |
         v          v          v         v          v          v
┌─────────────────────────────────────────────────────────────────────┐
|                         AGENT LAYER                                  |
├─────────────────────────────────────────────────────────────────────┤
|                                                                      |
|  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ |
|  | ScriptEnhancer  |    |    Director     |    |  TTSNarrator    | |
|  | (script_enhancer|    |   (director.py) |    | (tts_narrator   | |
|  |  .py)           |    |                 |    |  .py)           | |
|  | Transforms raw  |    | Reviews scripts |    | MiniMax Speech  | |
|  | transcript into |<-->| provides score  |    | Sentence-level  | |
|  | emotional arc   |    | & feedback      |    | generation      | |
|  └─────────────────┘    └─────────────────┘    └─────────────────┘ |
|                                                                      |
|  ┌─────────────────┐    ┌─────────────────┐                        |
|  | MusicGenerator  |    | ImageGenerator  |                        |
|  | (music_generator|    | (image_generator|                        |
|  |  .py)           |    |  .py)           |                        |
|  | Fal AI stable-  |    | Fal AI Flux     |                        |
|  | audio BGM       |    | Narrative-driven|                        |
|  | generation      |    | images          |                        |
|  └─────────────────┘    └─────────────────┘                        |
|                                                                      |
└─────────────────────────────────────────────────────────────────────┘
                                    |
                                    v
┌─────────────────────────────────────────────────────────────────────┐
|                        UTILITIES LAYER                               |
├─────────────────────────────────────────────────────────────────────┤
|  audio_mixer.py     | voice_styles.py    | video_assembler.py      |
|  VAD ducking        | Module-specific    | FFmpeg video            |
|  Crossfades         | voice processing   | assembly with           |
|  Normalization      | Speed/EQ/Reverb    | crossfade transitions   |
└─────────────────────────────────────────────────────────────────────┘
                                    |
                                    v
┌─────────────────────────────────────────────────────────────────────┐
|                       PIPELINE SCRIPTS                               |
├─────────────────────────────────────────────────────────────────────┤
|  advanced_bgm_pipeline_v2.py  | generate_clean_preview.py           |
|  9-segment daisy-chain        | Emotionally connective pacing       |
|  BGM generation               | Module preview generation           |
└─────────────────────────────────────────────────────────────────────┘
                                    |
                                    v
                        Final Podcast Video (MP4)
```

## Unified Entry Point: run_pipeline.py

The main entry point provides subcommands for each pipeline stage:

```bash
# Run the full pipeline
python run_pipeline.py full --input transcript.txt

# Individual stages
python run_pipeline.py enhance --input transcript.txt
python run_pipeline.py audio --script Output/enhanced_script.json
python run_pipeline.py visual --script Output/enhanced_script.json
python run_pipeline.py preview --module 1
python run_pipeline.py bgm --all

# Get help
python run_pipeline.py --help
python run_pipeline.py <command> --help
```

### Available Commands

| Command | Description | Key Arguments |
|---------|-------------|---------------|
| `enhance` | Enhance transcript with emotional arc | `--input`, `--output`, `--model` |
| `audio` | Generate TTS + BGM | `--script`, `--skip-tts`, `--skip-bgm` |
| `visual` | Generate narrative images | `--script` |
| `full` | Run complete pipeline | `--input`, `--model` |
| `preview` | Generate module preview | `--module`, `--hook`, `--all` |
| `bgm` | 9-segment BGM pipeline | `--generate`, `--stitch`, `--mix`, `--all` |

## Agent System

The system uses 5 specialized agents that work together:

### 1. ScriptEnhancer (`agents/script_enhancer.py`)
**Purpose:** Transforms raw transcripts into engaging, structured scripts

- Creates compelling 30-45 second hooks
- Structures content into 4 modules with emotional arcs
- Maps emotions (wonder, tension, triumph, etc.) to each chunk
- Extracts keywords, visual cues, and audio cues
- Target: 8-9 minutes total (1400-1600 words)

### 2. Director (`agents/director.py`)
**Purpose:** Reviews and scores enhanced scripts

- Evaluates hook quality, emotional arc, story flow
- Provides feedback for script revision
- Approval threshold: score >= 7
- Runs in loop with ScriptEnhancer until approved

### 3. TTSNarrator (`agents/tts_narrator.py`)
**Purpose:** Generates voice narration

- Uses MiniMax Speech-01-HD via Fal AI
- Sentence-level generation for precise control
- Handles pronunciation (e.g., "Bjork" -> "Byerk")

### 4. MusicGenerator (`agents/music_generator.py`)
**Purpose:** Generates background music

- Creates emotion-matched BGM using Fal AI stable-audio
- Supports daisy-chain conditioning for seamless transitions
- 9-segment architecture for full podcast

### 5. ImageGenerator (`agents/image_generator.py`)
**Purpose:** Generates narrative-driven images

- Uses Fal AI Flux model
- Cinematic photography style
- 16:9 landscape format
- 16 images total (2 hook + 14 modules)

## Voice Styles (Module-Specific)

Each module has a distinct delivery style applied via post-processing:

| Section | Style Name | Speed | Volume | EQ | Character |
|---------|------------|-------|--------|-----|-----------|
| Hook | The Intriguer | 1.05x | +2dB | Presence | Compelling, fast |
| Module 1 | The Biographer | 0.95x | 0dB | Warm | Nostalgic, measured |
| Module 2 | The Announcer | 1.08x | +3dB | Bright | Punchy, triumphant |
| Module 3 | The Punk Chronicler | 1.12x | +4dB | Edge | Raw, urgent |
| Module 4 | The Sage | 0.92x | +1dB | Full | Reflective, reverb |

## 9-Segment Daisy-Chain BGM Architecture

The BGM system uses audio-to-audio conditioning where each segment feeds into the next for seamless genre transitions.

### Segment Specification

| # | Name | Time | Phase | Goal |
|---|------|------|-------|------|
| 1 | The Hook | 0:00-0:45 | Origins | Icelandic ambient, cold mystery |
| 2 | The Bohemian Commune | 0:45-2:53 | Origins | Warm folk fusion, creative |
| 3 | The Pre-Build | 2:53-3:15 | Breakthrough | Transition to orchestral |
| 4 | Inflection 1: The Triumph | 3:15-3:45 | Breakthrough | Record deal swell |
| 5 | The Aftermath | 3:45-4:14 | Breakthrough | Ease down, prep for shift |
| 6 | Punk Intro | 4:14-4:40 | Punk Revolution | Introduce energy (no distortion) |
| 7 | Inflection 2: Energy Peak | 4:40-5:15 | Punk Revolution | Club/dance energy |
| 8 | Punk Fade Out | 5:15-6:00 | Punk Revolution | Cool down, transition |
| 9 | The Global Anthem | 6:00-8:28 | Global Mastery | Electronic pop finale |

### Daisy-Chain Conditioning Rules

- Each segment uses **last 10 seconds** of previous segment as input
- Input strength varies: 0.3-0.4 depending on desired genre shift
- 5-second buffer on each segment for crossfade stitching
- Fal AI max 47s per generation (longer segments chained internally)

### VAD-Based Ducking

- Voice Active: BGM at **-18 dB**
- Voice Silent: BGM at **-12 dB** (gentle rise)
- 100ms frame analysis for smooth transitions

## Key Files

### Entry Point
| File | Purpose | Usage |
|------|---------|-------|
| `run_pipeline.py` | **Unified entry point** | `python run_pipeline.py <command>` |

### Legacy Entry Points (still functional)
| File | Purpose | Usage |
|------|---------|-------|
| `transcribe.py` | Convert audio to text | `python transcribe.py` |
| `run_enhancement.py` | Script enhancement with Director review | `python run_enhancement.py --model sonnet` |
| `run_audio_enhancement.py` | Generate TTS + BGM | `python run_audio_enhancement.py` |
| `generate_clean_preview.py` | Generate paced module previews | `python generate_clean_preview.py --all` |

### BGM Pipeline Scripts
| File | Purpose | Usage |
|------|---------|-------|
| `reconstruct_bgm.py` | Simple BGM remix + voice-only mode | `python reconstruct_bgm.py --all --voice-only` |
| `advanced_bgm_pipeline_v2.py` | **9-segment daisy-chain (recommended)** | `python advanced_bgm_pipeline_v2.py --all` |

### Agent Modules (`agents/`)
| File | Class | Purpose |
|------|-------|---------|
| `script_enhancer.py` | `ScriptEnhancer` | Transforms transcript into engaging script with emotions, modules, hooks |
| `director.py` | `Director` | Reviews scripts and provides feedback (approval threshold: score >= 7) |
| `tts_narrator.py` | `TTSNarrator` | Generates speech using MiniMax Speech-01-HD (sentence-level) |
| `music_generator.py` | `MusicGenerator` | Generates emotion-matched BGM using Fal AI stable-audio |
| `image_generator.py` | `ImageGenerator` | Generates narrative-driven images using Fal AI Flux |

### Utilities (`utils/`)
| File | Purpose |
|------|---------|
| `audio_mixer.py` | Mixes TTS + BGM with crossfades, normalization |
| `voice_styles.py` | Module-specific voice style definitions and post-processing |
| `audio_design_generator.py` | Generates audio design metadata |
| `video_assembler.py` | Combines images + audio into video with crossfade transitions |

## Output Structure

```
Output/
├── enhanced_script.json           # Enhanced script with emotions, metadata
├── audio/
│   ├── tts/                       # TTS voice files (sentence-level)
│   │   ├── hook_sent_1.wav
│   │   ├── module_1_chunk_1_sent_1.wav
│   │   └── ...
│   ├── bgm/                       # Original BGM (one per module)
│   ├── bgm_v2_daisy/              # 9-segment daisy-chain BGM
│   │   ├── segment_01_the_hook.wav
│   │   ├── segment_02_the_bohemian_commune.wav
│   │   ├── segment_03_the_pre-build.wav
│   │   ├── segment_04_inflection_1_the_triumph.wav
│   │   ├── segment_05_the_aftermath.wav
│   │   ├── segment_06_punk_intro.wav
│   │   ├── segment_07_inflection_2_the_energy_peak.wav
│   │   ├── segment_08_punk_fade_out.wav
│   │   └── segment_09_inflection_3_the_global_anthem.wav
│   ├── previews_voice_only/       # Voice-only audio (no BGM)
│   │   ├── hook_preview_voice_only.mp3
│   │   ├── module_1_preview_voice_only.mp3
│   │   └── ...
│   ├── final_v2/                  # Final mixed audio
│   │   ├── bgm_stitched_v2.wav    # Stitched BGM with crossfades
│   │   └── final_podcast_v2.mp3   # Final audio with ducking
│   └── final_enhanced_v5.mp3      # Legacy final audio
└── Visuals Included/
    ├── hook/                      # Hook images
    ├── module_1/ - module_4/      # Module images
    ├── voice_only/                # Voice-only videos
    │   └── final_podcast_video_voice_only.mp4
    ├── v2_daisy/                  # Final video with daisy-chain BGM
    │   └── final_podcast_video_v2.mp4
    └── final_podcast_video.mp4    # Legacy final video
```

## Enhanced Script JSON Schema

```json
{
  "title": "Episode Title",
  "hook": {
    "text": "30-45 second compelling opener",
    "emotion": "intrigue",
    "duration_estimate_seconds": 35
  },
  "modules": [
    {
      "id": 1,
      "title": "Module Title",
      "emotion_arc": "wonder -> curiosity",
      "chunks": [
        {
          "text": "Chunk content...",
          "emotion": "wonder",
          "tension_level": 3,
          "keywords": ["keyword1", "keyword2"],
          "visual_cues": ["visual description"],
          "audio_cues": ["audio description"]
        }
      ]
    }
  ],
  "review_history": [...],
  "final_status": { "approved": true, "total_rounds": 1, "final_score": 8 }
}
```

## BGM Prompts by Segment

### Phase 1: Origins
```
Segment 1 (Hook): Cinematic ambient soundscape, Iceland atmosphere, glacial wind textures,
distant geothermal rumbling, minimal glass chimes, sense of mystery, cold but magical,
high fidelity, 70 BPM, reverb-heavy flute in distance.

Segment 2 (Bohemian): Warm acoustic folk fusion, gentle flute and acoustic guitar strumming,
experimental textures blending with organic sounds, curious and whimsical, soft rhythmic pulse,
creative and bohemian, 85 BPM, major key, sense of childhood wonder.
```

### Phase 2: Breakthrough
```
Segment 3 (Pre-Build): Building orchestral pop, piano arpeggios starting gently, confident
rhythm emerging, hopeful and bright, feeling of anticipation, crisp production, 95 BPM.

Segment 4 (Triumph): Triumphant orchestral swell, sweeping strings section, bright synthesizer
pads, major key, euphoric release, victory moment, rich and full sound, uplifting, 100 BPM.

Segment 5 (Aftermath): Orchestral pop settling down, steady rhythmic pulse, remaining hopeful
but less intense, transition to slightly edgier texture, 100 BPM.
```

### Phase 3: Punk Revolution (Softened)
```
Segment 6 (Punk Intro): Driving rhythmic bassline, fast-paced drums, new-wave energy,
clean electric guitar strumming (no distortion), high energy pulse, 120 BPM, mysterious and cool.

Segment 7 (Energy Peak): High energy alternative rock, driving drum beat, catchy bass groove,
upbeat and rebellious but polished, The Sugarcubes style, dynamic and fast, 125 BPM,
no harsh noise, smooth but powerful.

Segment 8 (Fade Out): Rhythmic drum groove continues, bassline becomes simpler, atmospheric
synthesizers entering, cooling down energy, transition towards electronic pop, 120 BPM.
```

### Phase 4: Global Mastery
```
Segment 9 (Global Anthem): Anthemic electronic pop, 90s house beat, sophisticated synthesizer,
celebratory and majestic, wide stadium sound, confident and polished, artistic freedom,
128 BPM, euphoric finale.
```

## Environment Variables

Required in `.env`:
```
FAL_KEY=your-fal-ai-key
ANTHROPIC_API_KEY=your-anthropic-key
MINIMAX_API_KEY=your-minimax-key  # For Speech-01-HD TTS
```

## API Models Used

| Component | Model | Notes |
|-----------|-------|-------|
| TTS | MiniMax Speech-01-HD | Via Fal AI, sentence-level generation |
| BGM | Fal AI stable-audio | Max 47s per generation, audio-to-audio conditioning |
| LLM | Claude claude-sonnet-4-20250514 | Script enhancement |
| Images | Fal AI Flux | Narrative-driven image generation |

## Common Workflows

### Full Pipeline (Recommended)
```bash
# Single command to run everything
python run_pipeline.py full --input transcript.txt
```

### Step-by-Step Pipeline
```bash
# 1. Enhance script (with Director review loop)
python run_pipeline.py enhance --input transcript.txt

# 2. Generate audio (TTS + BGM)
python run_pipeline.py audio --script Output/enhanced_script.json

# 3. Generate visuals
python run_pipeline.py visual --script Output/enhanced_script.json

# 4. Generate 9-segment daisy-chain BGM
python run_pipeline.py bgm --all
```

### Preview Workflow
```bash
# Generate previews for quality review
python run_pipeline.py preview --hook
python run_pipeline.py preview --module 1
python run_pipeline.py preview --all
```

### Legacy Commands (Still Supported)
```bash
# Transcribe audio (if needed)
python transcribe.py

# Script enhancement
python run_enhancement.py --model sonnet

# Audio generation
python run_audio_enhancement.py --sentence-level

# BGM pipeline
python advanced_bgm_pipeline_v2.py --all
```

## Script Duration Guidelines

Target: 8-9 minutes total (~1400-1600 words)
- **Hook**: 30-45 seconds (~100-150 words)
- **Each Module**: 2-2.5 minutes (~300-375 words)
- **4 Modules total**
- **3-4 chunks per module**

## Director Review Criteria

The Director agent scores scripts on:
1. **Hook Quality** (critical): Attention-grabbing, creates intrigue
2. **Emotional Arc** (critical): Roller-coaster experience, varied tension
3. **Story Flow**: Coherent narrative, natural transitions
4. **Metadata Quality**: Specific keywords, cinematic cues
5. **Module Structure**: Clear titles, appropriate distribution

**Approval**: Score >= 7 AND no critical criteria below 6

## Current Output (Bjork Podcast)

### Audio
**Final Audio:** `Output/audio/final_v2/final_podcast_v2.mp3`
**Duration:** 8 min 28 sec

| Section | Duration | Style |
|---------|----------|-------|
| Hook | 45s | The Intriguer |
| Module 1 | 128s | The Biographer |
| Module 2 | 81s | The Announcer |
| Module 3 | 106s | The Punk Chronicler |
| Module 4 | 148s | The Sage |

### Video
**Final Video:** `Output/Visuals Included/v2_daisy/final_podcast_video_v2.mp4`
**Duration:** 8 min 37 sec | **Resolution:** 1920x1080

| Section | Duration | Images | Visual Theme |
|---------|----------|--------|--------------|
| Hook | 45s | 2 | Stage spotlight -> Iceland landscape |
| Module 1 | 128s | 4 | Volcanic origin -> Commune -> Musical duality -> Aurora |
| Module 2 | 81s | 3 | Recording studio -> Album celebration -> Street scene |
| Module 3 | 106s | 3 | Punk club -> Experimental performance -> New beginning |
| Module 4 | 148s | 4 | TV spotlight -> Studio tension -> Solo liberation -> Full circle |

**Total:** 16 narrative-driven images

### BGM Evolution
| Time | Segment | Musical Style |
|------|---------|---------------|
| 0:00-0:45 | The Hook | Icelandic ambient, glacial |
| 0:45-2:53 | Bohemian Commune | Warm folk fusion |
| 2:53-3:15 | Pre-Build | Orchestral anticipation |
| 3:15-3:45 | Triumph Swell | Euphoric orchestral |
| 3:45-4:14 | Aftermath | Settling orchestral |
| 4:14-4:40 | Punk Intro | Driving new-wave |
| 4:40-5:15 | Energy Peak | Polished alt-rock |
| 5:15-6:00 | Punk Fade | Transitional |
| 6:00-8:28 | Global Anthem | Electronic pop finale |

## Known Issues and Fixes

1. **BGM noise at start**: Trim 500ms from BGM start, add 2s fade-in
2. **Pronunciation "Bjork"**: Preprocessed to "Byerk" in TTS
3. **Fixed pauses feel robotic**: Use variable pauses based on emotional role
4. **JSON parsing in prompts**: Use double curly braces `{{` `}}` in f-strings
5. **Audio cutoff at module transitions**: Removed `-shortest` FFmpeg flag in `video_assembler.py` and `reconstruct_bgm.py`
6. **Harsh punk section**: Replaced distorted/feral prompts with driving/rhythmic (clean guitars)

## Visual Enhancement (Narrative-Driven Images)

### Design Principles
1. **Images serve the narrative** - Each image has emotional reasoning tied to the script
2. **20-40 second average duration** - Long enough to register, not so long as to fatigue
3. **No person depictions** - Use settings, objects, landscapes, atmospheric imagery
4. **Static images with crossfade** - Simple transitions, no Ken Burns effect
5. **Visual continuity** - Color arcs and recurring motifs connect modules

### Recurring Visual Motifs
- **Iceland Landscape**: Appears in Hook (end), Module 1 (open/close), Module 4 (finale)
- **Performance Spaces**: School stage -> Punk club -> TV studio -> Solo studio
- **Color Progression**: Warm amber -> Cool blue -> Dark/gritty -> Bright -> Transcendent

### Image Generation
Images are generated using Fal AI Flux model with cinematic style suffix:
```python
CINEMATIC_STYLE = ', cinematic photography, documentary style, photorealistic, film grain, 35mm film aesthetic, professional lighting, high quality'
```

## Archive (Legacy Files)

The following files have been archived to `archive/` as they are superseded by newer implementations:

| File | Replacement |
|------|-------------|
| `advanced_bgm_pipeline.py` | `advanced_bgm_pipeline_v2.py` |
| `generate_final_v4.py` | `run_pipeline.py` |
| `apply_audio_effects_v3.py` | `utils/audio_mixer.py` |
| `regenerate_bgm.py` | `advanced_bgm_pipeline_v2.py` |
| `preview_module.py` | `generate_clean_preview.py` |

## Future Enhancements (Planned)

- **SFX Selector**: Add sound effects based on keywords (volcanic, ice crack, etc.)
- **Ken Burns Effect**: Optional subtle pan/zoom on images
- **Audio Surgery Effects**: Breath sounds, reverb tails, era-specific EQ
- **Subtitle Generation**: Auto-generate SRT subtitles synced to video
- **Thumbnail Generator**: Auto-generate video thumbnail from key frames
- **Multi-episode Support**: Batch processing for podcast series
