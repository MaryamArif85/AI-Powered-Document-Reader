from typing import Optional, Literal
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from pathlib import Path
import tempfile
from app.rag_service import RAGService
from app.document_loader import load_file
from app.ingest_service import IngestService
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(
    title="Grok + ChromaDB RAG API - With Prompt Styles + Upload",
    version="3.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("templates/index.html")

rag_service: Optional[RAGService] = None
ingest_service: Optional[IngestService] = None

class QuestionRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: Optional[int] = Field(default=None, ge=1, le=50)
    source: Optional[str] = None
    style: Literal["zero_shot", "few_shot", "role_based"] = Field(
        default="zero_shot",
        description="Prompting style: zero_shot, few_shot, role_based"
    )

@app.on_event("startup")
def startup() -> None:
    global rag_service, ingest_service
    print("Starting RAG service.")
    try:
        rag_service = RAGService()
        ingest_service = IngestService()
        print("RAG service started successfully.")
    except Exception as exc:
        print(f"Rag startup failed: {exc}")
        raise
    
@app.get("/health")
def health():
    return {
        "status": "ok",
        "indexed_chunks": 1161,
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "vector_db": "ChromaDB",
        "similarity": "cosine",
        "llm": "grok"
    }


@app.post("/rag/query")
def query_rag(payload: QuestionRequest):
    if rag_service is None:
        raise HTTPException(status_code=503, detail="RAG service is not ready.")
    try:
        return rag_service.ask(
            question=payload.question,
            top_k=payload.top_k,
            source=payload.source,
            style=payload.style,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@app.post("/rag/compare")
def compare_styles(payload: QuestionRequest):
    if rag_service is None:
        raise HTTPException(status_code=503, detail="RAG service is not ready.")

    comparison = {}
    sources = None
    for s in ["zero_shot", "few_shot", "role_based"]:
        res = rag_service.ask(
            question=payload.question,
            top_k=payload.top_k,
            source=payload.source,
            style=s
        )
        comparison[s] = res["answer"]
        if sources is None:
            sources = res["sources"]

    return {
        "question": payload.question,
        "comparison": comparison,
        "sources": sources
    }

@app.post("/rag/upload")
async def upload_document(file: UploadFile = File(...)):
    if rag_service is None or ingest_service is None:
        raise HTTPException(status_code=503, detail="RAG service is not ready.")

    filename = file.filename.lower()
    if not filename.endswith((".pdf", ".txt", ".md")):
        raise HTTPException(status_code=400, detail="Only pdf, txt, md allowed")

    try:
        content = await file.read()
        suffix = Path(file.filename).suffix

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        docs = load_file(tmp_path)

        for d in docs:
            d["source"] = file.filename

        if not docs:
            raise ValueError("File is empty or no text extracted")

        chunks_added = ingest_service.ingest_documents(docs)

        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        (data_dir / file.filename).write_bytes(content)

        tmp_path.unlink()

        return {
            "filename": file.filename,
            "file_type": suffix.replace(".",""),
            "status": "success",
            "chunks_indexed": chunks_added,
            "total_chunks_in_db": rag_service.store.count(),
            "message": f"Successfully indexed {file.filename}. You can now query it."
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}") from exc