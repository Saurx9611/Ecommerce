import asyncio
from abc import ABC, abstractmethod
from pydantic import BaseModel
from app.services.transcription_service import RawSegment

class DiarizedSegment(BaseModel):
    text: str
    start_time: float
    end_time: float
    confidence: float
    speaker_label: str

class SpeakerSummary(BaseModel):
    label: str
    display_name: str
    speaking_duration: float
    segment_count: int

class DiarizationResult(BaseModel):
    speakers: list[SpeakerSummary]
    segments: list[DiarizedSegment]

class SpeakerDiarizationService(ABC):
    @abstractmethod
    async def diarize(self, segments: list[RawSegment]) -> DiarizationResult:
        """Assigns speaker labels and computes speaking durations across segments."""
        pass


class MockSpeakerDiarizationService(SpeakerDiarizationService):
    """Deterministic development diarization service assigning multi-speaker turns."""
    async def diarize(self, segments: list[RawSegment]) -> DiarizationResult:
        await asyncio.sleep(0.3)  # Simulate diarization processing
        
        diarized_segments: list[DiarizedSegment] = []
        speaker_stats: dict[str, dict] = {
            "Speaker 1": {"duration": 0.0, "count": 0, "default_name": "Host (Alex)"},
            "Speaker 2": {"duration": 0.0, "count": 0, "default_name": "Guest (Dr. Sarah Chen)"},
        }

        # Alternate speakers across segments
        for idx, seg in enumerate(segments):
            speaker_label = "Speaker 1" if (idx % 2 == 0) else "Speaker 2"
            duration = seg.end_time - seg.start_time
            
            speaker_stats[speaker_label]["duration"] += duration
            speaker_stats[speaker_label]["count"] += 1
            
            diarized_segments.append(
                DiarizedSegment(
                    text=seg.text,
                    start_time=seg.start_time,
                    end_time=seg.end_time,
                    confidence=seg.confidence,
                    speaker_label=speaker_label
                )
            )

        speakers: list[SpeakerSummary] = [
            SpeakerSummary(
                label=lbl,
                display_name=data["default_name"],
                speaking_duration=round(data["duration"], 2),
                segment_count=data["count"]
            )
            for lbl, data in speaker_stats.items()
        ]

        return DiarizationResult(speakers=speakers, segments=diarized_segments)


def get_diarization_service() -> SpeakerDiarizationService:
    return MockSpeakerDiarizationService()
