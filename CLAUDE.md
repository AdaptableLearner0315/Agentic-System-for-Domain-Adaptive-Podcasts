# Nell Development Guidelines

**Author: Sarath**

Development rules and conventions for the Nell Podcast Enhancement System.

> **Architecture Reference**: See [ARCHITECTURE.md](./ARCHITECTURE.md) for system diagrams, component details, and data flows.

---

## Quick Reference

### Start Development Servers

```bash
# Backend (port 8000)
cd backend && uvicorn app.main:app --reload

# Frontend (port 3000)
cd frontend && npm run dev
```

### Run Full Pipeline (CLI)

```bash
# Normal mode (~2 min)
python run_pipeline.py full --input transcript.txt --mode normal

# Pro mode (~6 min)
python run_pipeline.py full --input transcript.txt --mode pro

# Generate from prompt
python run_pipeline.py full --prompt "History of electronic music" --mode normal
```

### Run Tests

```bash
# Backend
cd backend && pytest tests/unit -v

# Frontend
cd frontend && npm test
```

---

## Frontend Rules

### Component Structure
- One component per file in `frontend/src/components/`
- Use named exports: `export function ComponentName()`
- Props interface defined above component
- Keep components under 200 lines; extract sub-components if larger

### Hooks
- Custom hooks in `frontend/src/hooks/`
- Prefix with `use`: useGeneration, useProgress, useFileUpload
- Return object with named properties, not arrays
- Handle loading, error, and success states

### State Management
- Local state with useState for UI-only state
- Custom hooks for shared/complex state
- sessionStorage for cross-page data (e.g., prompt reuse)
- No global state library unless complexity demands it

### TypeScript
- Strict mode enabled
- All props must be typed (no `any`)
- Use `@/types` for shared types
- Prefer interfaces over types for objects

### API Calls
- All API calls through `frontend/src/lib/api.ts`
- Use typed request/response models from `@/types`
- Handle errors with try/catch and user-friendly messages

### Styling
- Use Tailwind CSS classes
- Follow dark theme conventions (bg-gray-900, text-gray-100)
- Responsive: mobile-first with sm/md/lg breakpoints

---

## Backend Rules

### Route Structure
- Routes in `backend/app/routes/` by resource
- Use dependency injection for services
- Return Pydantic response models
- Document with OpenAPI (docstrings become docs)

### Service Layer
- Business logic in `backend/app/services/`
- Services are stateless; state in JobManager
- Async functions for I/O operations
- Type hints on all function signatures

### Error Handling
- Use HTTPException with appropriate status codes:
  - 400: Bad request (validation errors)
  - 404: Resource not found
  - 500: Caught by global exception handler
- Return ErrorResponse model for consistency

### Pydantic Models
- Request models in `backend/app/models/requests.py`
- Response models in `backend/app/models/responses.py`
- Use Field() for validation and documentation
- Enums in `backend/app/models/enums.py`

### WebSocket
- Progress updates via `/api/ws/{job_id}/progress`
- Send JSON with: `stage`, `progress`, `message`, `eta_seconds`
- Handle connection cleanup on disconnect

---

## Unit Test Rules

### Frontend (Jest/React Testing Library)
- File: `ComponentName.test.tsx` in `__tests__/` directory
- Test user interactions, not implementation details
- Mock API calls with `jest.mock('@/lib/api')`
- Test loading, error, and success states

Example:
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { ComponentName } from '../ComponentName';

jest.mock('@/lib/api');

describe('ComponentName', () => {
  it('handles user click', async () => {
    render(<ComponentName />);
    fireEvent.click(screen.getByRole('button'));
    expect(await screen.findByText('Success')).toBeInTheDocument();
  });
});
```

### Backend (pytest)
- File: `test_<module>.py` in `tests/unit/`
- Use fixtures in `conftest.py` for shared setup
- Mock external APIs (fal, anthropic)
- Test edge cases and error paths

Example:
```python
import pytest
from unittest.mock import patch

@pytest.fixture
def mock_fal_client():
    with patch('agents.music_generator.fal_client') as mock:
        yield mock

def test_generates_bgm(mock_fal_client):
    mock_fal_client.run.return_value = {'audio_file': {'url': 'test.wav'}}
    result = generator.generate_segment(prompt="ambient")
    assert result.endswith('.wav')
```

### Coverage Requirements
- Minimum 70% coverage for new code
- Critical paths require 90%
- Run: `pytest --cov` or `npm test -- --coverage`

---

## End-to-End Test Rules

### Integration Tests
- File: `tests/integration/test_<flow>.py`
- Test complete request/response cycles
- Use TestClient for FastAPI endpoints
- Mock external AI services, not internal services

### WebSocket Testing
```python
from fastapi.testclient import TestClient

def test_progress_websocket(client: TestClient, job_id: str):
    with client.websocket_connect(f"/api/ws/{job_id}/progress") as ws:
        data = ws.receive_json()
        assert "stage" in data
```

### File Upload Testing
- Use `UploadFile` with in-memory BytesIO
- Test multiple file formats (txt, pdf, docx)
- Verify cleanup after test

---

## Code Modularization

### Single Responsibility
- One class/function per concern
- Agents do one thing: enhance, generate, validate
- Utilities are pure functions where possible

### Import Structure
```python
# Standard library
import os
from pathlib import Path

# Third-party
import fal_client
from pydantic import BaseModel

# Local
from agents.base_agent import BaseAgent
from utils.audio_mixer import mix_audio
```

### Shared Utilities Location
- `utils/` for cross-cutting concerns
- `config/` for configuration and mappings
- `assets/` for pre-generated resources

### Avoiding Circular Dependencies
- Agents import utils, not vice versa
- Services import agents, not vice versa
- Use dependency injection for cross-service calls

---

## Docstring Standards

### Python (Google-style)
```python
def generate_bgm(prompt: str, duration: int = 30) -> Path:
    """Generate background music from a text prompt.

    Args:
        prompt: Text description of desired music style.
        duration: Length in seconds (max 47).

    Returns:
        Path to the generated audio file.

    Raises:
        ValueError: If duration exceeds API limit.
    """
```

### TypeScript (JSDoc)
```typescript
/**
 * Fetches job status from the API.
 * @param jobId - The unique job identifier
 * @returns Promise resolving to job status object
 * @throws Error if job not found
 */
async function getJobStatus(jobId: string): Promise<JobStatus> {
```

### Required For
- All public functions and classes
- All API route handlers
- Complex private functions

---

## Low Latency Guidelines

### Parallel Execution
```python
# Python - concurrent.futures
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(generate_tts, chunks))

# TypeScript - Promise.all
const results = await Promise.all(
  chunks.map(chunk => generateTTS(chunk))
);
```

### Caching Strategies
- Cache API responses with TTL (5 min for mode configs)
- Pre-generate common assets (voice phrases, music stems)
- Use sessionStorage for UI state persistence

### Streaming Responses
- Use WebSocket for long-running operations
- Stream progress updates every 1-2 seconds
- Include ETA in progress messages

### Avoiding Blocking
- Use async/await for all I/O operations
- Offload heavy processing to background tasks
- Set appropriate timeouts (30s API, 5min pipeline)

---

## Self-Evolution Protocol

When you fix a bug, determine if it's a recurring pattern that others might hit.

**Add to "Known Issues and Fixes" if:**
- The bug could recur in similar code
- The fix involves a non-obvious workaround
- The issue stems from external API behavior
- The problem is related to timing/async/race conditions

**Do NOT add if:**
- It's a simple typo or one-off mistake
- The fix is obvious from the error message
- It's already documented elsewhere

**Format:**
```
N. **<Short description>**: <Root cause> → <Fix applied>
```

---

## Known Issues and Fixes

1. **BGM noise at start**: Raw BGM has artifacts → Trim 500ms from start, add 2s fade-in
2. **Pronunciation "Bjork"**: TTS mispronounces → Preprocess to "Byerk" in text
3. **Fixed pauses feel robotic**: Uniform gaps → Use variable pauses based on emotional role
4. **JSON parsing in prompts**: Single braces break f-strings → Use double curly braces `{{` `}}`
5. **Audio cutoff at module transitions**: FFmpeg `-shortest` flag → Remove flag in video_assembler.py
6. **Harsh punk section**: Distorted BGM prompts → Replace with driving/rhythmic (clean guitars)
7. **WebSocket disconnect on tab switch**: Browser suspends connection → Implement reconnection logic with exponential backoff
8. **CORS error on port 3001**: Default only allows 3000 → Add 3001 to cors_origins in config.py

---

## Environment Setup

### Required API Keys (`.env`)
```bash
FAL_KEY=your-fal-ai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

### Backend Environment
```bash
# .env
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
OUTPUT_DIR=./Output
UPLOAD_DIR=./uploads
```

### Frontend Environment
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## Common CLI Commands

### Pipeline Commands
```bash
# Full pipeline
python run_pipeline.py full --input transcript.txt --mode normal

# Individual stages
python run_pipeline.py enhance --input transcript.txt
python run_pipeline.py audio --script Output/enhanced_script.json
python run_pipeline.py visual --script Output/enhanced_script.json
python run_pipeline.py bgm --all
```

### Development Commands
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest tests --cov=app

# Frontend
cd frontend
npm install
npm run dev
npm test
npm run build
```

---

## Git Conventions

### Commit Messages
- Use imperative mood: "Add feature" not "Added feature"
- Keep subject under 72 characters
- Reference issue numbers: "Fix #123: WebSocket reconnection"

### Branch Naming
- Feature: `feature/add-multi-speaker`
- Bugfix: `fix/websocket-disconnect`
- Refactor: `refactor/extract-architecture-docs`

### PR Guidelines
- One feature/fix per PR
- Include test coverage
- Update relevant documentation
