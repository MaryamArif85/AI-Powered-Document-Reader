from typing import Iterable, List
from sentence_transformers import SentenceTransformer
from.config import settings

def clean_text(text: str) -> str:
    return text.encode('utf-8', 'ignore').decode('utf-8', 'ignore')

class EmbeddingService:
    def __init__(self) -> None:
        self.model = SentenceTransformer(settings.embedding_model)

    def embed(self, texts: Iterable[str]) -> List[List[float]]:
        raw_list = list(texts)
        clean_texts = []
        for t in raw_list:
            if t is None:
                continue
            t = clean_text(str(t)).strip()
            if not t:
                continue
            clean_texts.append(t)

        if not clean_texts:
            return []

        
        vectors = self.model.encode(
            clean_texts,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False,
        )
        return vectors.tolist()

    def embed_one(self, text: str) -> List[float]:
        result = self.embed([text])
        return result[0] if result else []