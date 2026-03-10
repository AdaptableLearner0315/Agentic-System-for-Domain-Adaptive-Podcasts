# Nell Podcast System - Architecture

**Author: Sarath**

This document describes the architecture and system design of the Nell Podcast Enhancement System.

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

### Version History

- **v2:** Normal Mode (~2 min) and Pro Mode (~6 min) with parallel execution, multi-format input, progress streaming
- **v3:** Emotion mapping and multi-speaker support (15 emotions, 4 speaker formats)
- **v4:** Prompt-to-Podcast flow (Generation, Enhancement, Hybrid modes)
- **v5:** Web Interface (FastAPI backend + React/Next.js frontend)

---

## High-Level Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SMART INPUT HANDLER                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  USER INPUT: --prompt "Topic" --files doc.pdf --guidance "Style"    │
│                        │              │               │              │
│                        ▼              ▼               ▼              │
│               ┌─────────────────────────────────────────────┐       │
│               │        SmartInputHandler.process()          │       │
│               │                                             │       │
│               │  IF prompt only:                            │       │
│               │    → ContentGeneratorAgent.generate()       │       │
│               │    → Pure generation from scratch           │       │
│               │                                             │       │
│               │  IF files only:                             │       │
│               │    → InputRouter.extract() (existing)       │       │
│               │    → Pure enhancement                       │       │
│               │                                             │       │
│               │  IF prompt + files:                         │       │
│               │    → Extract files as reference             │       │
│               │    → Generate content informed by files     │       │
│               │    → Hybrid mode                            │       │
│               └─────────────────────────────────────────────┘       │
│                                    │                                 │
│                                    ▼                                 │
│              ExtractedContent { text, source_type, metadata }       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    MODE SELECTOR                                     │
│               Normal (fast) │ Pro (quality)                          │
└─────────────────────────────────────────────────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                  ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│     NORMAL PIPELINE      │    │      PRO PIPELINE        │
│   Target: 90-120 sec     │    │   Target: 5-8 min        │
│                          │    │                          │
│ • Parallel execution     │    │ • Director review loop   │
│ • Chunk-level TTS        │    │ • Sentence-level TTS     │
│ • 3-segment BGM          │    │ • 9-segment daisy-chain  │
│ • 4 library images       │    │ • 16 narrative images    │
│ • No voice styling       │    │ • Full voice styling     │
└──────────────────────────┘    └──────────────────────────┘
              │                                  │
              └────────────────┬────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PROGRESS STREAMING                                │
│  Real-time updates • ETA estimation • Preview content               │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                     Final Podcast Video (MP4)
```

---

## Detailed Component Architecture

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

---

## Web UI Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js/React)                        │
├─────────────────────────────────────────────────────────────────────┤
│  PromptInput → FileUpload → ModeSelector → ProgressTracker          │
│                                                                      │
│  Hooks: useGeneration, useProgress, useFileUpload                   │
│  State: job status, progress, result                                │
└─────────────────────────────────────────────────────────────────────┘
                               │
                    REST API + WebSocket
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                               │
├─────────────────────────────────────────────────────────────────────┤
│  Routes:     /api/pipelines/*  /api/files/*  /api/config/*          │
│  Services:   PipelineService   FileService   JobManager             │
│  WebSocket:  /api/ws/{job_id}/progress                              │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   EXISTING PIPELINES                                │
│            NormalPipeline  │  ProPipeline                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Agent System

The system uses 8 specialized agents:

| Agent | File | Purpose |
|-------|------|---------|
| **ScriptEnhancer** | `agents/script_enhancer.py` | Transforms raw transcripts into engaging scripts with emotional arcs, hooks, 4 modules |
| **Director** | `agents/director.py` | Reviews scripts, provides scores and feedback (approval threshold: score >= 7) |
| **TTSNarrator** | `agents/tts_narrator.py` | Generates voice narration using MiniMax Speech-01-HD (sentence-level) |
| **MusicGenerator** | `agents/music_generator.py` | Generates emotion-matched BGM using Fal AI stable-audio with daisy-chain conditioning |
| **ImageGenerator** | `agents/image_generator.py` | Generates narrative-driven images using Fal AI Flux (16:9 landscape, 16 total) |
| **EmotionValidator** | `agents/emotion_validator.py` | Validates emotion consistency across pipeline, checks tension-emotion alignment |
| **SpeakerAssignmentAgent** | `agents/speaker_assignment_agent.py` | Assigns speakers for multi-speaker formats (interview, co-hosts, narrator+characters) |
| **ContentGeneratorAgent** | `agents/content_generator_agent.py` | Generates original podcast content from topic prompts using Claude |

---

## Mode Comparison

| Feature | Normal Mode | Pro Mode |
|---------|-------------|----------|
| **Target Time** | 90-120 seconds | 5-8 minutes |
| **TTS Granularity** | Chunk-level (15 calls) | Sentence-level (80-100 calls) |
| **BGM Segments** | 3 parallel | 9 daisy-chain |
| **Images** | 4 key moments | 16 narrative |
| **Director Review** | No | Yes (3 rounds) |
| **Voice Styling** | Single adaptive | 5 personas |
| **Emotion Voice Sync** | No | Yes (15 emotions) |
| **Emotion Image Align** | No | Yes (color/mood) |
| **Multi-Speaker** | No | Yes (4 formats) |
| **Emotion Validation** | No | Yes |
| **Parallelization** | Full (10 workers) | Partial |

---

## 9-Segment Daisy-Chain BGM Architecture

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

---

## Emotion Mapping System (Pro Mode)

### Supported Emotions (15 total)

| Emotion | Speed | Emphasis | Visual Style |
|---------|-------|----------|--------------|
| wonder | 0.95x | soft | ethereal blues, expansive |
| curiosity | 1.00x | moderate | warm amber, inviting |
| tension | 1.02x | moderate | stark contrasts, dramatic |
| triumph | 1.05x | strong | warm golds, heroic |
| melancholy | 0.90x | soft | muted blues, intimate |
| intrigue | 0.98x | moderate | mysterious purples |
| excitement | 1.10x | strong | vibrant, energetic |
| reflection | 0.92x | soft | sepia, contemplative |
| restlessness | 1.05x | moderate | edgy contrasts |
| explosive_energy | 1.15x | strong | intense reds, powerful |
| rebellion | 1.12x | strong | punk aesthetics, raw |
| liberation | 1.08x | strong | open skies, freeing |
| experimentation | 1.00x | moderate | creative, artistic |
| mastery | 0.95x | moderate | sophisticated, refined |
| intensity | 1.08x | strong | focused, powerful |

### Data Flows

```
Emotion-Voice: Script Emotion → TTS Speed Adjustment → Post-processing EQ/Compression → Final Voice

Emotion-Image: Chunk Emotion → Visual Style Lookup → Enhanced Prompt → Fal AI Flux → Emotion-aligned Image
```

---

## Multi-Speaker System (Pro Mode)

### Available Formats

| Format | Speakers | Detection Patterns | Use Case |
|--------|----------|-------------------|----------|
| `single` | narrator | (default) | Documentary, storytelling |
| `interview` | host, guest | Q:, A:, "interview" | Expert interviews |
| `co_hosts` | host_1, host_2 | "we", "let's", "together" | Conversational podcasts |
| `narrator_characters` | narrator, character | quotes, "said" | Narrative with dialogue |

### Available Voices (MiniMax Speech-01-HD)

| Voice Key | Voice ID | Description |
|-----------|----------|-------------|
| `female_friendly` | Friendly_Female_English | Warm, engaging |
| `female_professional` | Professional_Female_English | Clear, authoritative |
| `female_energetic` | Energetic_Female_English | Upbeat, dynamic |
| `male_friendly` | Friendly_Male_English | Warm, approachable |
| `male_professional` | Professional_Male_English | Clear, authoritative |
| `male_energetic` | Energetic_Male_English | Upbeat, dynamic |

---

## Voice Styles (Module-Specific)

| Section | Style Name | Speed | Volume | EQ | Character |
|---------|------------|-------|--------|-----|-----------|
| Hook | The Intriguer | 1.05x | +2dB | Presence | Compelling, fast |
| Module 1 | The Biographer | 0.95x | 0dB | Warm | Nostalgic, measured |
| Module 2 | The Announcer | 1.08x | +3dB | Bright | Punchy, triumphant |
| Module 3 | The Punk Chronicler | 1.12x | +4dB | Edge | Raw, urgent |
| Module 4 | The Sage | 0.92x | +1dB | Full | Reflective, reverb |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/pipelines/generate` | Start generation job |
| `GET` | `/api/pipelines/{id}/status` | Get job progress |
| `GET` | `/api/pipelines/{id}/result` | Get final result |
| `POST` | `/api/pipelines/{id}/cancel` | Cancel running job |
| `GET` | `/api/pipelines/` | List all jobs |
| `POST` | `/api/files/upload` | Upload file |
| `POST` | `/api/files/upload-url` | Extract from URL |
| `GET` | `/api/files/{id}` | Get file info |
| `DELETE` | `/api/files/{id}` | Delete file |
| `GET` | `/api/config/modes` | Get mode configs |
| `GET` | `/api/outputs/download/{id}` | Download output |
| `WS` | `/api/ws/{id}/progress` | Real-time progress stream |

---

## Directory Structure

### Backend

```
backend/
├── app/
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # Pydantic settings
│   ├── dependencies.py         # Dependency injection
│   ├── routes/
│   │   ├── pipelines.py        # /api/pipelines/*
│   │   ├── files.py            # /api/files/*
│   │   ├── config.py           # /api/config/*
│   │   └── outputs.py          # /api/outputs/*
│   ├── models/
│   │   ├── requests.py         # Pydantic request models
│   │   ├── responses.py        # Pydantic response models
│   │   └── enums.py            # Shared enums
│   ├── services/
│   │   ├── pipeline_service.py # Pipeline orchestration
│   │   ├── file_service.py     # File handling
│   │   ├── job_manager.py      # Job state tracking
│   │   └── progress_adapter.py # ProgressStream adapter
│   └── websockets/
│       └── progress.py         # Real-time updates
├── tests/
│   ├── conftest.py             # Shared fixtures
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
└── requirements.txt
```

### Frontend

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx            # Main generation page
│   │   ├── layout.tsx          # Root layout
│   │   ├── globals.css         # Tailwind globals
│   │   └── jobs/[id]/page.tsx  # Job result page
│   ├── components/
│   │   ├── PromptInput.tsx     # Main input area
│   │   ├── FileUpload.tsx      # Drag-drop upload
│   │   ├── ModeSelector.tsx    # Normal/Pro toggle
│   │   ├── ProgressTracker.tsx # Real-time progress
│   │   ├── OutputPlayer.tsx    # Video/audio player
│   │   └── Header.tsx          # App header
│   ├── hooks/
│   │   ├── useGeneration.ts    # Generation state
│   │   ├── useProgress.ts      # WebSocket progress
│   │   └── useFileUpload.ts    # File upload logic
│   ├── lib/
│   │   ├── api.ts              # API client
│   │   ├── websocket.ts        # WebSocket client
│   │   └── utils.ts            # Utility functions
│   └── types/
│       └── index.ts            # TypeScript types
├── package.json
├── tailwind.config.js
└── next.config.js
```

### Pipelines & Agents

```
pipelines/
├── normal_pipeline.py          # Fast 90-120 second generation
└── pro_pipeline.py             # High-quality 5-8 minute generation

agents/
├── script_enhancer.py          # Script transformation
├── director.py                 # Script review
├── tts_narrator.py             # Voice generation
├── music_generator.py          # BGM generation
├── image_generator.py          # Image generation
├── emotion_validator.py        # Emotion validation
├── speaker_assignment_agent.py # Multi-speaker assignment
└── content_generator_agent.py  # Content generation

utils/
├── audio_mixer.py              # Audio mixing with VAD ducking
├── voice_styles.py             # Module-specific voice styles
├── video_assembler.py          # FFmpeg video assembly
├── smart_input_handler.py      # Input routing
├── parallel_executor.py        # Async batch execution
├── input_router.py             # Multi-format routing
├── progress_stream.py          # Progress streaming
└── extractors/                 # Format-specific extractors
    ├── text_extractor.py
    ├── pdf_extractor.py
    ├── word_extractor.py
    ├── audio_extractor.py
    ├── video_extractor.py
    └── url_extractor.py

config/
├── modes.py                    # Normal/Pro mode definitions
├── user_config.py              # User preferences
├── emotion_voice_mapping.py    # Emotion → voice parameters
├── emotion_visual_mapping.py   # Emotion → visual style
└── speaker_config.py           # Speaker formats and voices
```

---

## Output Structure

```
Output/
├── enhanced_script.json           # Enhanced script with emotions, metadata
├── audio/
│   ├── tts/                       # TTS voice files (sentence-level)
│   ├── bgm/                       # Original BGM (one per module)
│   ├── bgm_v2_daisy/              # 9-segment daisy-chain BGM
│   ├── previews_voice_only/       # Voice-only audio (no BGM)
│   ├── final_v2/                  # Final mixed audio
│   │   ├── bgm_stitched_v2.wav
│   │   └── final_podcast_v2.mp3
│   └── final_enhanced_v5.mp3      # Legacy final audio
└── Visuals Included/
    ├── hook/                      # Hook images
    ├── module_1/ - module_4/      # Module images
    ├── voice_only/                # Voice-only videos
    ├── v2_daisy/                  # Final video with daisy-chain BGM
    │   └── final_podcast_video_v2.mp4
    └── final_podcast_video.mp4    # Legacy final video
```

---

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

---

## Script Duration Guidelines

Target: 8-9 minutes total (~1400-1600 words)
- **Hook**: 30-45 seconds (~100-150 words)
- **Each Module**: 2-2.5 minutes (~300-375 words)
- **4 Modules total**
- **3-4 chunks per module**

---

## Director Review Criteria

The Director agent scores scripts on:
1. **Hook Quality** (critical): Attention-grabbing, creates intrigue
2. **Emotional Arc** (critical): Roller-coaster experience, varied tension
3. **Story Flow**: Coherent narrative, natural transitions
4. **Metadata Quality**: Specific keywords, cinematic cues
5. **Module Structure**: Clear titles, appropriate distribution

**Approval**: Score >= 7 AND no critical criteria below 6

---

## API Models Used

| Component | Model | Notes |
|-----------|-------|-------|
| TTS | MiniMax Speech-01-HD | Via Fal AI, sentence-level generation |
| BGM | Fal AI stable-audio | Max 47s per generation, audio-to-audio conditioning |
| LLM | Claude claude-sonnet-4-20250514 | Script enhancement |
| Images | Fal AI Flux | Narrative-driven image generation |

---

## Visual Enhancement Design Principles

1. **Images serve the narrative** - Each image has emotional reasoning tied to the script
2. **20-40 second average duration** - Long enough to register, not so long as to fatigue
3. **No person depictions** - Use settings, objects, landscapes, atmospheric imagery
4. **Static images with crossfade** - Simple transitions, no Ken Burns effect
5. **Visual continuity** - Color arcs and recurring motifs connect modules

### Image Generation Style

```python
CINEMATIC_STYLE = ', cinematic photography, documentary style, photorealistic, film grain, 35mm film aesthetic, professional lighting, high quality'
```

---

## Future Enhancements (Planned)

- **SFX Selector**: Add sound effects based on keywords (volcanic, ice crack, etc.)
- **Ken Burns Effect**: Optional subtle pan/zoom on images
- **Audio Surgery Effects**: Breath sounds, reverb tails, era-specific EQ
- **Subtitle Generation**: Auto-generate SRT subtitles synced to video
- **Thumbnail Generator**: Auto-generate video thumbnail from key frames
- **Multi-episode Support**: Batch processing for podcast series
- **Asset Pre-generation CLI**: Command to pre-generate asset libraries
