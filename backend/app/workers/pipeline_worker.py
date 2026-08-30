import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.episode import Episode
from app.models.speaker import Speaker
from app.models.transcript import TranscriptSegment
from app.models.embedding import ChunkEmbedding
from app.models.processing_job import ProcessingJob
from app.models.notification import Notification
from app.models.episode_insight import EpisodeInsight
from app.models.project import Project
from app.services.transcription_service import get_transcription_service
from app.services.diarization_service import get_diarization_service
from app.services.chunking_service import get_chunking_service
from app.services.embedding_service import get_embedding_service
from app.services.insight_service import get_insight_service
from app.storage.storage_service import storage_service

logger = logging.getLogger("pipeline_worker")

class PipelineWorker:
    def __init__(self):
        self.transcription_service = get_transcription_service()
        self.diarization_service = get_diarization_service()
        self.chunking_service = get_chunking_service()
        self.embedding_service = get_embedding_service()
        self.insight_service = get_insight_service()

    async def _update_job_stage(self, db: AsyncSession, job_id: int, episode_id: int, stage: str, progress: float, status: str = "processing"):
        # Update Job
        stmt_job = (
            update(ProcessingJob)
            .where(ProcessingJob.id == job_id)
            .values(current_stage=stage, progress=progress, status=status)
        )
        # Update Episode
        stmt_ep = (
            update(Episode)
            .where(Episode.id == episode_id)
            .values(status=stage if status != "completed" else "completed")
        )
        await db.execute(stmt_job)
        await db.execute(stmt_ep)
        await db.commit()

    async def process_episode(self, episode_id: int, job_id: int):
        """Asynchronously executes the 6-stage AI ingestion pipeline for a podcast episode."""
        async with AsyncSessionLocal() as db:
            try:
                # 1. Fetch Episode
                episode = await db.get(Episode, episode_id)
                if not episode:
                    logger.error(f"Episode {episode_id} not found for processing.")
                    return

                # Stage 1: Upload / Pre-processing
                await self._update_job_stage(db, job_id, episode_id, "upload", 10.0)
                audio_path = storage_service.get_absolute_path(episode.audio_url)

                # Stage 2: Transcription
                await self._update_job_stage(db, job_id, episode_id, "transcribing", 30.0)
                transcript_res = await self.transcription_service.transcribe(audio_path)
                
                # Update duration if detected
                if transcript_res.duration > 0:
                    episode.duration = transcript_res.duration
                    episode.language = transcript_res.language
                    await db.commit()

                # Stage 3: Speaker Diarization
                await self._update_job_stage(db, job_id, episode_id, "speaker_detection", 50.0)
                diarization_res = await self.diarization_service.diarize(transcript_res.segments)

                # Persist Speakers
                speaker_map: dict[str, Speaker] = {}
                for spk_summary in diarization_res.speakers:
                    speaker = Speaker(
                        episode_id=episode.id,
                        label=spk_summary.label,
                        display_name=spk_summary.display_name,
                        speaking_duration=spk_summary.speaking_duration,
                        segment_count=spk_summary.segment_count
                    )
                    db.add(speaker)
                    await db.flush()
                    speaker_map[spk_summary.label] = speaker

                # Persist Transcript Segments
                segment_entities: list[TranscriptSegment] = []
                for seq_idx, d_seg in enumerate(diarization_res.segments):
                    speaker = speaker_map.get(d_seg.speaker_label)
                    seg_entity = TranscriptSegment(
                        episode_id=episode.id,
                        speaker_id=speaker.id if speaker else None,
                        text=d_seg.text,
                        start_time=d_seg.start_time,
                        end_time=d_seg.end_time,
                        sequence_number=seq_idx,
                        confidence=d_seg.confidence
                    )
                    db.add(seg_entity)
                    segment_entities.append(seg_entity)

                await db.flush()

                # Stage 4: Speaker-Aware Temporal Chunking
                await self._update_job_stage(db, job_id, episode_id, "chunking", 65.0)
                chunks = self.chunking_service.chunk(diarization_res.segments)

                # Stage 5: Vector Embedding Generation
                await self._update_job_stage(db, job_id, episode_id, "embedding", 80.0)
                chunk_texts = [c.chunk_text for c in chunks]
                embeddings_vectors = await self.embedding_service.get_embeddings(chunk_texts)

                # Stage 6: Vector Indexing in pgvector
                await self._update_job_stage(db, job_id, episode_id, "indexing", 90.0)
                for chunk, vector in zip(chunks, embeddings_vectors):
                    # Find corresponding segment if available
                    seg_id = segment_entities[chunk.segment_index].id if chunk.segment_index < len(segment_entities) else None
                    embedding_entity = ChunkEmbedding(
                        episode_id=episode.id,
                        segment_id=seg_id,
                        speaker_label=chunk.speaker_label,
                        chunk_text=chunk.chunk_text,
                        start_time=chunk.start_time,
                        end_time=chunk.end_time,
                        embedding=vector
                    )
                    db.add(embedding_entity)

                # Stage 7: Generate Episode Insights
                full_text = " ".join(s.text for s in transcript_res.segments)
                insights_res = await self.insight_service.generate_insights(episode.title, full_text)
                
                insight_entity = EpisodeInsight(
                    episode_id=episode.id,
                    overview=insights_res.overview,
                    target_competencies=insights_res.target_competencies,
                    core_tech_stack=insights_res.core_tech_stack,
                    architectural_blueprint=insights_res.architectural_blueprint,
                    resume_transformation=insights_res.resume_transformation
                )
                db.add(insight_entity)

                # Mark Completed
                now = datetime.now(timezone.utc)
                stmt_finish_job = (
                    update(ProcessingJob)
                    .where(ProcessingJob.id == job_id)
                    .values(
                        current_stage="complete",
                        progress=100.0,
                        status="completed",
                        completed_at=now
                    )
                )
                stmt_finish_ep = (
                    update(Episode)
                    .where(Episode.id == episode.id)
                    .values(status="completed", processed_at=now)
                )
                await db.execute(stmt_finish_job)
                await db.execute(stmt_finish_ep)

                # Create Notification for User
                project = await db.get(Project, episode.project_id)
                if project:
                    notification = Notification(
                        user_id=project.user_id,
                        title=f"Episode Processed: {episode.title}",
                        message=f"Transcription, speaker diarization, and vector indexing completed for '{episode.title}'.",
                        type="processing_success",
                        is_read=False
                    )
                    db.add(notification)

                await db.commit()
                logger.info(f"Successfully processed episode {episode_id}")

            except Exception as ex:
                logger.exception(f"Processing failed for episode {episode_id}: {ex}")
                now = datetime.now(timezone.utc)
                stmt_err_job = (
                    update(ProcessingJob)
                    .where(ProcessingJob.id == job_id)
                    .values(
                        status="failed",
                        error_message=str(ex),
                        completed_at=now
                    )
                )
                stmt_err_ep = (
                    update(Episode)
                    .where(Episode.id == episode_id)
                    .values(status="failed")
                )
                await db.execute(stmt_err_job)
                await db.execute(stmt_err_ep)
                await db.commit()


pipeline_worker = PipelineWorker()
