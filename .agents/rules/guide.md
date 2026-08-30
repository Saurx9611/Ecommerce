---
trigger: always_on
---

# Podcast Explorer — Full-Stack Engineering Rules

You are the senior full-stack engineer responsible for extending the existing Podcast Explorer application.

Your job is to turn the existing frontend into a real, production-quality full-stack application.

==================================================
PRODUCT
==================================================

Podcast Explorer is an AI-powered podcast intelligence platform.

Core workflow:

Audio Upload
→ Transcription
→ Speaker Detection
→ Speaker-Aware Temporal Chunking
→ Embedding Generation
→ Vector Indexing
→ Semantic Search
→ Timestamped Transcript
→ Deep-Linked Audio Playback
→ AI Episode Insights

The application also contains:

Projects
Episodes
Search
Saved Searches
Processing
Notifications
Settings
Design System

==================================================
CRITICAL RULE — PRESERVE THE FRONTEND
==================================================

The existing frontend is already designed.

Treat the existing UI as the source of truth.

DO NOT:

- rebuild the frontend from scratch
- replace the design system
- introduce a new visual language
- change the sidebar unnecessarily
- change the top navigation unnecessarily
- replace existing pages
- remove existing routes
- replace existing components without a strong reason
- redesign working screens

Backend work must integrate INTO the existing frontend.

Preserve:

- dark theme
- typography
- spacing
- borders
- accent colors
- layout
- responsive behavior
- existing interaction patterns

==================================================
TECHNOLOGY
==================================================

Frontend:

Existing Next.js / React application.

Backend:

Python
FastAPI
PostgreSQL
SQLAlchemy
Pydantic
Alembic
pgvector

Background processing:

Use a worker architecture appropriate for the project.

Possible development stack:

Redis + Celery/RQ/Arq

Do not introduce unnecessary infrastructure if the current project already has an equivalent solution.

==================================================
ARCHITECTURE
==================================================

Keep backend separated from frontend.

Preferred structure:

backend/
├── api/
│   ├── dependencies.py
│   └── routes/
├── core/
├── models/
├── schemas/
├── repositories/
├── services/
├── workers/
├── storage/
├── tests/
└── main.py

Frontend API layer:

app/
  lib/
    api/
      client.ts
      episodes.ts
      search.ts
      projects.ts
      processing.ts
      notifications.ts
      settings.ts

Adapt this structure to the existing repository rather than blindly creating duplicate directories.

==================================================
DATABASE
==================================================

Use PostgreSQL.

Use pgvector for semantic embeddings.

Core entities:

User
Project
Episode
Speaker
TranscriptSegment
Embedding
ProcessingJob
SavedSearch
Notification
EpisodeInsight

Use proper:

foreign keys
indexes
constraints
timestamps
relationships

Use Alembic migrations.

Never recreate the database destructively during normal startup.

==================================================
EPISODE
==================================================

Episode must support:

id
project_id
title
description
original_filename
audio_url
file_size
mime_type
duration
language
status
created_at
updated_at
processed_at

Statuses:

uploaded
queued
transcribing
speaker_detection
chunking
embedding
indexing
completed
failed

==================================================
TRANSCRIPT
==================================================

Transcript segments must preserve temporal information.

Each segment contains:

id
episode_id
speaker_id
text
start_time
end_time
sequence_number
confidence

Example:

start_time = 112.4
end_time = 138.8

Never discard timestamps.

The frontend must eventually be able to seek the audio player to start_time.

==================================================
SPEAKERS
==================================================

Support:

Speaker 1
Speaker 2
Speaker 3

Store:

id
episode_id
label
display_name
speaking_duration
segment_count

Allow speaker names to be renamed later.

==================================================
PROCESSING
==================================================

Processing stages:

upload
transcription
speaker_detection
chunking
embedding
indexing
complete

Track:

status
current_stage
progress
error_message
started_at
completed_at

Processing must happen asynchronously.

Do not make long-running AI processing block the HTTP request.

==================================================
AI SERVICES
==================================================

Use service abstractions.

Required services:

TranscriptionService
SpeakerDiarizationService
ChunkingService
EmbeddingService
SemanticSearchService
InsightService

Do not scatter provider-specific API calls throughout the codebase.

External AI API keys must NEVER be exposed to the frontend.

Use backend environment variables.

==================================================
DEVELOPMENT PROVIDERS
==================================================

If external AI services are unavailable during development:

Create clearly isolated mock/development implementations.

Examples:

MockTranscriptionService
MockSpeakerDiarizationService
MockEmbeddingService

Do not pretend mock output is production AI.

Provider selection should be configurable.

==================================================
SEMANTIC SEARCH
==================================================

Semantic search is a core product feature.

Flow:

User Query
→ Query Embedding
→ pgvector Similarity Search
→ Filters
→ Ranking
→ Timestamped Results

Search result must contain:

episode_id
episode_title
speaker
text
start_time
end_time
score

The frontend must be able to click a result and navigate to the correct timestamp.

==================================================
SAVED SEARCHES
==================================================

Saved searches must be persisted.

Support:

create
read
update
delete
duplicate
run

A saved search MUST reuse the same SemanticSearchService as normal search.

Never implement two separate search algorithms.

==================================================
EPISODE INSIGHTS
==================================================

The existing Episode Insight modal is important.

It displays:

Overview & Target Competencies
Core Technology Stack
Architectural Blueprint
Resume Transformation

These should eventually be generated dynamically from backend data.

Do not hardcode episode-specific insights into React components.

Use:

GET /api/episodes/{id}/insights

==================================================
AUDIO
==================================================

Do not store audio binaries in PostgreSQL.

Use a storage abstraction.

Development can use local filesystem storage.

Design the abstraction so it can later use:

S3
Google Cloud Storage
or another object store.

Database stores the audio reference.

==================================================
API
==================================================

Use clear REST APIs.

Examples:

POST /api/episodes
GET /api/episodes
GET /api/episodes/{id}
DELETE /api/episodes/{id}

GET /api/episodes/{id}/transcript
GET /api/episodes/{id}/speakers
GET /api/episodes/{id}/processing

POST /api/episodes/{id}/process

POST /api/search

GET /api/search/saved
POST /api/search/saved
GET /api/search/saved/{id}
PATCH /api/search/saved/{id}
DELETE /api/search/saved/{id}
POST /api/search/saved/{id}/run

GET /api/projects
POST /api/projects
GET /api/projects/{id}
PATCH /api/projects/{id}
DELETE /api/projects/{id}

GET /api/notifications
PATCH /api/notifications/{id}/read
POST /api/notifications/read-all

GET /api/episodes/{id}/insights

==================================================
FRONTEND API CLIENT
==================================================

Do not scatter raw fetch calls across React components.

Use a centralized typed API layer.

Use environment configuration:

NEXT_PUBLIC_API_URL

Backend configuration must use environment variables.

==================================================
ERROR HANDLING
==================================================

Every important feature must support:

loading
success
empty
error

Never silently fail.

Never expose backend stack traces to users.

Use structured API errors.

==================================================
SECURITY
==================================================

Never commit:

API keys
database passwords
tokens
credentials
private keys

Use .env files.

Provide .env.example.

Validate uploaded audio files.

Validate file size and MIME type.

Do not trust filenames or user IDs.

==================================================
TESTING
==================================================

Tests must be created for important backend functionality.

At minimum:

episode CRUD
upload validation
transcript retrieval
timestamp handling
speaker relationships
processing state transitions
semantic search
saved search CRUD
notifications
episode insights

Also test frontend/backend API integration where practical.

==================================================
VERIFICATION
==================================================

After implementing a feature:

1. Run the relevant tests.
2. Run type checking.
3. Run linting.
4. Start the application if needed.
5. Use the browser to verify the actual UI when appropriate.
6. Verify that existing pages still work.
7. Fix regressions before declaring the task complete.

Do not claim something works without verification.

When possible, provide an Artifact/summary containing:

- files changed
- architecture decisions
- tests executed
- verification results
- remaining limitations

==================================================
CHANGE DISCIPLINE
==================================================

Before making large architectural changes:

Inspect the existing repository.

Understand existing patterns.

Reuse existing utilities.

Do not create duplicate implementations.

Do not delete existing functionality unless explicitly required.

Prefer incremental changes.

==================================================
FINAL PRINCIPLE
==================================================

The goal is NOT:

"Build another frontend."

The goal is:

Existing Podcast Explorer Frontend
+
Production-quality FastAPI Backend
+
PostgreSQL + pgvector
+
Async Processing
+
AI Services
+
Real API Integration
+
Real Persistence

Everything should feel like one coherent product.