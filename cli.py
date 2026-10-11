from app.rag_service import RAGService
import argparse

def main() -> None:
    parser = argparse.ArgumentParser(description="Grok + ChromaDB RAG CLI")
    parser.add_argument("--style", type=str, default="zero_shot",
                        choices=["zero_shot", "few_shot", "role_based"],
                        help="Prompt style to use")
    args = parser.parse_args()

    rag = RAGService()
    print(f"\nGrok + ChromaDB RAG - Style: {args.style}")
    print("Embeddings: local SentenceTransformers")
    print("LLM: xAI Grok")
    print("Type 'exit' to quit.\n")

    while True:
        question = input("Question: ").strip()
        if question.lower() in {"exit", "quit", "q"}:
            break
        if not question:
            continue
        try:
            
            result = rag.ask(question=question, style=args.style)
            print(f"\nANSWER [{result.get('style')}]")
            print(result["answer"])
            print("\nRETRIEVED SOURCES")
            for source in result["sources"]:
                print(f'- {source["source"]} | page={source["page"] or "n/a"} | chunk={source["chunk"]} | distance={source["distance"]:.4f}')
            print()
        except Exception as exc:
            print(f"\nERROR: {exc}\n")

if __name__ == "__main__":
    main()