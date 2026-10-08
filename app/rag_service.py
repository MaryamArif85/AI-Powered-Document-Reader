from typing import Any, Dict, List, Optional
from.config import settings
from.embedding_service import EmbeddingService
from.grok_service import GrokService
from.vector_store import ChromaVectorStore
from.prompt_service import PromptService, PromptStyle

class RAGService:
    def __init__(self) -> None:
        self.embedder = EmbeddingService()
        self.grok = GrokService()
        self.store = ChromaVectorStore()
        self.prompt_service = PromptService()

    @staticmethod
    def build_context(results: List[Dict[str, Any]]) -> str:
        blocks: List[str] = []
        for index, result in enumerate(results, start=1):
            metadata = result["metadata"]
            source = metadata.get("source", "unknown")
            page = metadata.get("page", 0)
            chunk = metadata.get("chunk", 0)
            page_text = str(page) if page else "n/a"
            blocks.append(f"[SOURCE {index}]\nFile: {source}\nPage: {page_text}\nChunk: {chunk}\n\n{result['text']}\n")
        return "\n".join(blocks)

    def ask(self, question: str, top_k: Optional[int] = None, source: Optional[str] = None, style: PromptStyle = "zero_shot") -> Dict[str, Any]:
        if not question.strip():
            raise ValueError("Question cannot be empty.")
        if self.store.count() == 0:
            raise RuntimeError("ChromaDB is empty. Run ingest.py first.")

        # Clean surrogates - your 1159 fix
        clean_q = question.encode('utf-8','ignore').decode('utf-8','ignore')
        query_embedding = self.embedder.embed_one(clean_q)

        where = {"source": source} if source else None
        retrieved = self.store.query(query_embedding=query_embedding, top_k=top_k or settings.top_k, where=where)
        context = self.build_context(retrieved)

        # NOW USE YOUR PROMPT_SERVICE WITH STYLE!
        prompt = self.prompt_service.build_prompt(question=question, context=context, style=style)

        answer = self.grok.generate(prompt)

        sources = []
        for result in retrieved:
            metadata = result["metadata"]
            sources.append({"source": metadata.get("source", "unknown"), "page": metadata.get("page", 0), "chunk": metadata.get("chunk", 0), "distance": result["distance"], "text": result["text"]})

        return {"question": question, "answer": answer, "sources": sources, "style": style}
