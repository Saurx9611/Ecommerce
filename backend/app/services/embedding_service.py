import math
import hashlib
from abc import ABC, abstractmethod
from app.core.config import settings

class EmbeddingService(ABC):
    @abstractmethod
    async def get_embedding(self, text: str) -> list[float]:
        """Generates a dense vector embedding for the input text."""
        pass

    @abstractmethod
    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Batch generates vector embeddings for a list of texts."""
        pass


class MockEmbeddingService(EmbeddingService):
    """Deterministic development embedding generator using semantic token hashing & L2 normalization."""
    def __init__(self, dimension: int = settings.EMBEDDING_DIMENSION):
        self.dimension = dimension

    def _generate_deterministic_vector(self, text: str) -> list[float]:
        # Hash text words to produce semantic vector distribution
        vector = [0.0] * self.dimension
        words = text.lower().split()
        if not words:
            words = ["empty"]

        for word in words:
            # Deterministic hash seed
            sha = hashlib.sha256(word.encode("utf-8")).hexdigest()
            for i in range(min(16, self.dimension)):
                idx = int(sha[i*2:(i+1)*2], 16) % self.dimension
                val = (int(sha[i:i+4], 16) % 1000) / 1000.0 - 0.5
                vector[idx] += val

        # L2 Normalize vector
        magnitude = math.sqrt(sum(x * x for x in vector))
        if magnitude > 0:
            vector = [x / magnitude for x in vector]
        else:
            vector[0] = 1.0

        return vector

    async def get_embedding(self, text: str) -> list[float]:
        return self._generate_deterministic_vector(text)

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [self._generate_deterministic_vector(t) for t in texts]


def get_embedding_service() -> EmbeddingService:
    return MockEmbeddingService()
