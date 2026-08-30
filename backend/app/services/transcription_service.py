import asyncio
from abc import ABC, abstractmethod
from pydantic import BaseModel

class RawSegment(BaseModel):
    text: str
    start_time: float
    end_time: float
    confidence: float = 0.98

class TranscriptionResult(BaseModel):
    language: str
    duration: float
    segments: list[RawSegment]

class TranscriptionService(ABC):
    @abstractmethod
    async def transcribe(self, audio_file_path: str) -> TranscriptionResult:
        """Transcribes an audio file into timestamped segments."""
        pass


class MockTranscriptionService(TranscriptionService):
    """Deterministic, high-quality development transcription service for podcast audio."""
    async def transcribe(self, audio_file_path: str) -> TranscriptionResult:
        await asyncio.sleep(0.5)  # Simulate model inference latency
        
        sample_segments = [
            RawSegment(
                text="Welcome back to the Podcast Explorer Deep Dive. Today we're exploring high-concurrency systems, distributed caching, and vector indexing for multimedia intelligence.",
                start_time=0.0,
                end_time=12.4,
                confidence=0.99
            ),
            RawSegment(
                text="When you're building an event-driven ingestion pipeline, the hardest part is not just transcribing audio—it's speaker-aware temporal chunking so that semantic vector search preserves the contextual boundary of who said what and when.",
                start_time=12.5,
                end_time=29.8,
                confidence=0.97
            ),
            RawSegment(
                text="Exactly. If you arbitrarily cut audio at every 500 tokens, you sever speaker dialogue mid-sentence. You must group speech turns by speaker and align them with exact millisecond timestamps.",
                start_time=30.0,
                end_time=48.2,
                confidence=0.96
            ),
            RawSegment(
                text="Let's dive into pgvector and vector embeddings. How do you ensure sub-50ms semantic search queries across thousands of podcast episodes?",
                start_time=48.5,
                end_time=62.0,
                confidence=0.98
            ),
            RawSegment(
                text="By generating 768-dimensional normalized embeddings for each temporal window, indexing them with HNSW or IVFFlat cosine distance, and combining vector similarity with relational project filtering.",
                start_time=62.2,
                end_time=84.6,
                confidence=0.99
            ),
            RawSegment(
                text="And when the user clicks a search result in the frontend, the deep-linked audio player immediately seeks to that exact start_time. That completes the intelligent search experience.",
                start_time=84.8,
                end_time=102.5,
                confidence=0.98
            ),
            RawSegment(
                text="To wrap up, AI-driven episode insights can synthesize architectural blueprints, competency matrices, and technical summaries directly from the indexed transcripts.",
                start_time=102.8,
                end_time=124.0,
                confidence=0.97
            ),
        ]
        return TranscriptionResult(
            language="en",
            duration=124.0,
            segments=sample_segments
        )


def get_transcription_service() -> TranscriptionService:
    # Pluggable: Can initialize GeminiTranscriptionService if API key is provided
    return MockTranscriptionService()
