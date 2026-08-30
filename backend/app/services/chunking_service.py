from abc import ABC, abstractmethod
from pydantic import BaseModel
from app.services.diarization_service import DiarizedSegment

class TemporalChunk(BaseModel):
    chunk_text: str
    speaker_label: str
    start_time: float
    end_time: float
    segment_index: int

class ChunkingService(ABC):
    @abstractmethod
    def chunk(self, segments: list[DiarizedSegment], max_duration_sec: float = 60.0, overlap_sec: float = 10.0) -> list[TemporalChunk]:
        """Performs speaker-aware temporal chunking over timestamped diarized segments."""
        pass


class SpeakerAwareTemporalChunkingService(ChunkingService):
    def chunk(self, segments: list[DiarizedSegment], max_duration_sec: float = 60.0, overlap_sec: float = 10.0) -> list[TemporalChunk]:
        if not segments:
            return []

        chunks: list[TemporalChunk] = []
        
        # Group contiguous speech by the same speaker or temporal window
        current_speaker: str | None = None
        current_texts: list[str] = []
        chunk_start: float = 0.0
        chunk_end: float = 0.0
        first_seg_idx: int = 0

        for idx, seg in enumerate(segments):
            if current_speaker is None:
                current_speaker = seg.speaker_label
                chunk_start = seg.start_time
                chunk_end = seg.end_time
                current_texts = [seg.text]
                first_seg_idx = idx
            elif seg.speaker_label == current_speaker and (seg.end_time - chunk_start) <= max_duration_sec:
                # Contiguous segment from same speaker within temporal window
                current_texts.append(seg.text)
                chunk_end = seg.end_time
            else:
                # Flush previous chunk
                chunks.append(
                    TemporalChunk(
                        chunk_text=f"[{current_speaker}] " + " ".join(current_texts),
                        speaker_label=current_speaker,
                        start_time=round(chunk_start, 2),
                        end_time=round(chunk_end, 2),
                        segment_index=first_seg_idx
                    )
                )
                # Start new chunk
                current_speaker = seg.speaker_label
                chunk_start = seg.start_time
                chunk_end = seg.end_time
                current_texts = [seg.text]
                first_seg_idx = idx

        # Flush final chunk
        if current_texts and current_speaker is not None:
            chunks.append(
                TemporalChunk(
                    chunk_text=f"[{current_speaker}] " + " ".join(current_texts),
                    speaker_label=current_speaker,
                    start_time=round(chunk_start, 2),
                    end_time=round(chunk_end, 2),
                    segment_index=first_seg_idx
                )
            )

        return chunks


def get_chunking_service() -> ChunkingService:
    return SpeakerAwareTemporalChunkingService()
