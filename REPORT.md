# AI-Powered Document Reader - Technical Report
### RAG System with Semantic Search, ChromaDB and Prompt Comparison

**Project:** AI-powered-document-reader  
**Stack:** Sentence-Transformers all-MiniLM-L6-v2 + ChromaDB + Groq (openai/gpt-oss-20b) + FastAPI + Vanilla JS  
**Indexed:** 1161 chunks from 5 documents (3 PDFs + 2 TXT)  
**Date:** October 2026

---

## 1. Abstract
This project implements a full Retrieval-Augmented Generation (RAG) pipeline that answers user queries from private documents with grounded citations and similarity scores. Unlike keyword search, it uses semantic search via vector embeddings (384-dim) and cosine similarity to retrieve meaning, not just exact words. The system supports three prompting styles (zero_shot, few_shot, role_based) compared side-by-side with shared retrieved sources, and an optional upload toggle for custom PDF/TXT/MD documents.

Key proof: UI displays `Sim: 72.49% | Dist: 0.275` for each retrieved chunk, proving vector similarity, not BM25.

## 2. Objectives
- Implement end-to-end RAG: Load -> Chunk -> Embed -> Store -> Query -> Retrieve -> Generate
- Prove semantic search vs keyword search with scores
- Compare prompting styles effect on same question and same context
- Provide traceability via citations [filename p.page c.chunk]
- Support optional custom document upload

## 3. System Architecture

    User Question
        |
        v
    Embedding (all-MiniLM-L6-v2 -> 384 vector)
        |
        v
    ChromaDB Semantic Search (cosine, n_results=3, returns distances)
        |
        v
    Prompt Builder (3 variants)
        |
        v
    Groq LLM (openai/gpt-oss-20b)
        |
        v
    Answer + Sources [file + page + chunk + similarity % + distance + preview]

Components in `app/`:
- `document_loader.py`: Loads PDFs with PyMuPDF, preserves page numbers
- `embedding_service.py`: SentenceTransformer model
- `chroma_service.py`: Persistent Chroma collection `knowledge_base`, cosine space
- `ingest_service.py`: Chunking with RecursiveCharacterTextSplitter (1000/200)
- `prompt_service.py`: Builds zero_shot, few_shot, role_based prompts
- `grok_service.py`: Groq client
- `rag_service.py`: Orchestrates query -> embedding -> search -> prompt -> llm

## 4. Part 2: Embeddings & Semantic Search

### 4.1 Documents
Located in `data/`:
- DLSummary.pdf
- fine-tuning-lora-qlora.pdf
- Hands-on-Machine-Learning book.pdf
- lora_notes.txt
- rag_notes.txt
Total: 1161 chunks after splitting.

### 4.2 Chunking Strategy
    RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
Reason: 1000 balances context retention and embedding quality. 200 overlap prevents context loss at boundaries. Preserves page metadata for citation.

### 4.3 Embedding Model
Model: `sentence-transformers/all-MiniLM-L6-v2`
- Dimension: 384
- Why: Fast, lightweight, good for semantic search, runs locally, 80MB
- Normalization: L2 normalized for cosine similarity

Code:

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    vectors = model.encode(chunks, show_progress_bar=True, normalize_embeddings=True)

### 4.4 Vector Storage
ChromaDB PersistentClient at `chroma_db/`
Collection: `knowledge_base`
Metadata per chunk: filename, page, chunk_id, text preview
Distance metric: cosine

### 4.5 Semantic Search
Query is embedded with same model:

    q_vec = model.encode(question)
    result = collection.query(query_embeddings=[q_vec], n_results=3, include=["documents","metadatas","distances"])

Conversion:

    similarity = (1 - distance) * 100
    Example: distance 0.275 -> similarity 72.49%

UI shows both Sim % and Dist to prove it is vector search.

### 4.6 Semantic vs Keyword Search

| Aspect | Keyword BM25 | Semantic (Implemented) |
|---|---|---|
| Matching | Exact token overlap | Cosine similarity of meaning vectors |
| Synonyms | cheap car != affordable automobile | cheap car = affordable automobile (0.88) |
| Paraphrase Query | Fails if words differ | Retrieves conceptually similar |
| Example | Query "efficient fine-tuning" misses doc saying "LoRA reduces params 10000x" | Retrieves it with 0.89 similarity |
| Hallucination | High (no context) | Low (grounded in retrieved chunks) |

Why Semantic is Critical for RAG: User questions are phrased differently than documents. Semantic retrieval finds relevant meaning, giving LLM correct context to avoid hallucination.

## 5. Part 3: Prompting Styles Comparison

Endpoint: `POST /rag/compare` returns same retrieved sources for all 3 styles, different prompts.

**1. zero_shot:**
    Answer based on context only. If not found, say not enough info. Cite sources as [filename p.page].
- Baseline, strict grounding.

**2. few_shot:**
    Includes 2 QA examples with citations format.
    Context: {context}
    Q: What is LoRA? A: LoRA is... [file p.2]
    Q: What is RAG? A: RAG is... [file p.1]
    Now answer: {question}
- Shows model how to cite and structure.

**3. role_based:**
    You are AI analyst and researcher expert in ML. Provide structured analysis with sections, bullet points, pros/cons. Use context only. Cite sources.
- More analytical, structured output.

Model: Groq `openai/gpt-oss-20b` - fast inference, good instruction following.

Demo comparison query: "What is deep learning?"
- zero_shot gives direct definition
- few_shot gives definition with explicit page citations
- role_based gives sections: Overview, Difference, Efficiency, Use Cases

Screenshot: `images/02-compare-3-styles.png`

## 6. API Design
- GET / : Frontend UI
- GET /health : {status, indexed_chunks, embedding_model, vector_db, similarity, llm}
- POST /rag/query : {question, style, top_k, use_uploaded}
- POST /rag/compare : {question, top_k} -> {answers: {zero_shot, few_shot, role_based}, shared_sources}
- POST /rag/upload : multipart PDF/TXT/MD -> ingests, returns chunk count
- GET /docs : Swagger auto-doc

## 7. Frontend Features
- Indexed chunks badge (1161)
- Ask box + style dropdown
- Toggle "Use your own documents?" hides/shows drag & drop (bonus requirement)
- Single answer view with citations
- Compare view: 3 columns equal height + Shared Retrieved Sources on top with similarity
- Drag & drop upload with progress
- Mobile responsive

## 8. Results & Evaluation

**Functional:**
- Health endpoint returns 1161 chunks indexed
- Query "what is overfitting" retrieves Hands-on-Machine-Learning book chunks with 72.49% similarity even without exact phrase match in question
- Citations like [Hands-on-Machine-Learning book.pdf p.34 c.12] present in all answers
- Compare shows prompting affects tone and structure but retrieval stays same

**Quantitative:**
- Ingestion time: ~45 sec for 5 docs (including embedding)
- Query latency: ~0.3 sec retrieval + 1.5 sec Groq generation
- Embedding dim: 384, cosine distance 0.27-0.45 for relevant chunks (65-73% similarity)

**Screenshots:**
1. `01-ask.png` - Ask interface
2. `02-compare-3-styles.png` - Main proof of semantic scores + 3 styles
3. `03-upload-toggle.png` - Optional upload feature
4. `04-single-answer-with-citation.png` - Citation grounding
5. `05-health-api.png` - Vector DB status

## 9. Challenges & Solutions
- Issue: Health endpoint 500 due to import -> Fixed with safe count fallback
- Issue: Prompt result window not scrollable -> Added max-height + overflow-y
- Issue: Upload always visible -> Added checkbox toggle
- Issue: Similarity not shown -> Added Sim % and Dist calculation from Chroma distance

## 10. Future Work
- Reranking with cross-encoder
- Hybrid search (BM25 + semantic)
- Streaming answers
- Chat history
- Evaluation metrics (faithfulness, context precision)

## 11. Conclusion
System fully implements RAG with semantic search proof (similarity scores), 3 prompting style comparison with shared sources, citations, and custom upload toggle. ChromaDB persistent storage ensures 1161 chunks remain indexed. Groq LLM provides fast grounded answers. UI proves semantic search via displayed Sim % and Dist, distinguishing it from keyword search and reducing hallucination.

## 12. References
- Sentence-Transformers: all-MiniLM-L6-v2
- ChromaDB Documentation
- Groq API - openai/gpt-oss-20b
- LangChain RecursiveCharacterTextSplitter
- RAG paper: Lewis et al. 2020