import hashlib
from typing import Dict, List
from.chunker import chunk_documents
from.config import settings
from.document_loader import load_directory
from.embedding_service import EmbeddingService
from.vector_store import ChromaVectorStore

def clean_surrogates(text: str) -> str:
    # Removes \ud835 and other broken math characters
    return text.encode('utf-8', 'ignore').decode('utf-8', 'ignore')

def make_chunk_id(item: Dict) -> str:
    txt = clean_surrogates(item.get("text",""))
    raw = f'{item["source"]}|{item.get("page", 0)}|{item["chunk"]}|{txt}'
    # ignore errors here too
    return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()

class IngestService:
    def __init__(self) -> None:
        self.embedder = EmbeddingService()
        self.store = ChromaVectorStore()

    def _clean_batch(self, batch: List[Dict]) -> List[Dict]:
        cleaned = []
        for item in batch:
            txt = item.get("text")
            if txt is None:
                continue
            if not isinstance(txt, str):
                txt = str(txt)
            # CRITICAL FIX: remove surrogates
            txt = clean_surrogates(txt)
            txt = txt.strip()
            if not txt or len(txt) < 10:
                continue
            if len(txt) > 5000:
                txt = txt[:5000]
            new_item = item.copy()
            new_item["text"] = txt
            cleaned.append(new_item)
        return cleaned

    def ingest(self, directory: str = "./data", reset: bool = False) -> Dict:
        if reset:
            self.store.reset_collection()

        raw_documents = load_directory(directory)
        chunks = chunk_documents(raw_documents)

        if not chunks:
            return {"documents_loaded": len(raw_documents), "chunks_upserted": 0, "collection_count": self.store.count()}

        batch_size = settings.embedding_batch_size
        inserted = 0

        for start in range(0, len(chunks), batch_size):
            batch = chunks[start:start + batch_size]
            batch = self._clean_batch(batch)
            if not batch:
                continue
            texts = [item["text"] for item in batch]
            embeddings = self.embedder.embed(texts)

            if not embeddings:
                continue
            if len(embeddings)!= len(batch):
                batch = batch[:len(embeddings)]

            ids = [make_chunk_id(item) for item in batch]
            texts = [item["text"] for item in batch]
            metadatas: List[Dict] = [{"source": item["source"], "page": int(item.get("page", 0)), "chunk": int(item["chunk"]), "embedding_model": settings.embedding_model} for item in batch]

            self.store.upsert(ids=ids, texts=texts, metadatas=metadatas, embeddings=embeddings)
            inserted += len(batch)
            print(f"Embedded/stored {inserted}/{len(chunks)} chunks")

        return {"documents_loaded": len(raw_documents), "chunks_upserted": inserted, "collection_count": self.store.count(), "embedding_model": settings.embedding_model}

    def ingest_documents(self, raw_documents: List[Dict]) -> int:
        chunks = chunk_documents(raw_documents)
        if not chunks:
            return 0
        batch_size = settings.embedding_batch_size
        inserted = 0
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start:start + batch_size]
            batch = self._clean_batch(batch)
            if not batch:
                continue
            texts = [item["text"] for item in batch]
            embeddings = self.embedder.embed(texts)
            if not embeddings or len(embeddings)!= len(batch):
                if embeddings:
                    batch = batch[:len(embeddings)]
                else:
                    continue
            ids = [make_chunk_id(item) for item in batch]
            texts = [item["text"] for item in batch]
            metadatas: List[Dict] = [{"source": item["source"], "page": int(item.get("page", 0)), "chunk": int(item["chunk"]), "embedding_model": settings.embedding_model} for item in batch]
            self.store.upsert(ids=ids, texts=texts, metadatas=metadatas, embeddings=embeddings)
            inserted += len(batch)
        return inserted

IngestionService = IngestService