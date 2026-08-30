import pytest
from app.services.chunking_service import SpeakerAwareTemporalChunkingService
from app.services.diarization_service import DiarizedSegment
from app.services.embedding_service import MockEmbeddingService

def test_speaker_aware_temporal_chunking():
    chunker = SpeakerAwareTemporalChunkingService()
    
    segments = [
        DiarizedSegment(text="Hello and welcome.", start_time=0.0, end_time=5.0, confidence=0.99, speaker_label="Speaker 1"),
        DiarizedSegment(text="Today we talk about pgvector.", start_time=5.1, end_time=12.0, confidence=0.98, speaker_label="Speaker 1"),
        DiarizedSegment(text="Thanks for having me.", start_time=12.5, end_time=18.0, confidence=0.97, speaker_label="Speaker 2"),
        DiarizedSegment(text="Let's explain vector indexing.", start_time=18.2, end_time=25.0, confidence=0.99, speaker_label="Speaker 2"),
    ]
    
    chunks = chunker.chunk(segments, max_duration_sec=30.0)
    assert len(chunks) == 2
    assert chunks[0].speaker_label == "Speaker 1"
    assert chunks[0].start_time == 0.0
    assert chunks[0].end_time == 12.0
    assert "[Speaker 1]" in chunks[0].chunk_text
    
    assert chunks[1].speaker_label == "Speaker 2"
    assert chunks[1].start_time == 12.5
    assert chunks[1].end_time == 25.0
    assert "[Speaker 2]" in chunks[1].chunk_text

@pytest.mark.asyncio
async def test_mock_embedding_service_dimensions():
    embedder = MockEmbeddingService(dimension=768)
    vector = await embedder.get_embedding("Distributed vector search with pgvector")
    assert len(vector) == 768
    # Test L2 normalization (sum of squares ~ 1.0)
    mag_sq = sum(x * x for x in vector)
    assert abs(mag_sq - 1.0) < 1e-4
