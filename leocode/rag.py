"""RAG system using ChromaDB for document retrieval."""

import os
import hashlib
from pathlib import Path
from typing import Optional

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False


def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    overlap = min(overlap, chunk_size - 1)
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


class RAGStore:
    def __init__(self, persist_dir: str, collection: str = "leocode_docs"):
        self.persist_dir = persist_dir
        self.collection_name = collection
        self._client = None
        self._col = None
        if HAS_CHROMA:
            os.makedirs(persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )

    def _get_collection(self):
        if self._col is None and self._client:
            self._col = self._client.get_or_create_collection(
                self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._col

    def add_document(self, file_path: str, content: str, chunk_size: int = 1000) -> int:
        col = self._get_collection()
        if not col:
            return 0
        chunks = _chunk_text(content, chunk_size)
        ids = []
        docs = []
        metas = []
        for i, chunk in enumerate(chunks):
            doc_id = hashlib.md5(f"{file_path}:{i}".encode()).hexdigest()
            ids.append(doc_id)
            docs.append(chunk)
            metas.append({"source": file_path, "chunk": i, "total_chunks": len(chunks)})
        if ids:
            col.upsert(ids=ids, documents=docs, metadatas=metas)
        return len(ids)

    def add_directory(self, dir_path: str, extensions: list[str] | None = None, chunk_size: int = 1000) -> int:
        exts = extensions or [".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".go", ".java", ".c", ".cpp",
                             ".h", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini"]
        total = 0
        p = Path(dir_path)
        for f in p.rglob("*"):
            if f.is_file() and f.suffix.lower() in exts and f.stat().st_size < 1_000_000:
                try:
                    content = f.read_text(errors="ignore")
                    total += self.add_document(str(f), content, chunk_size)
                except Exception:
                    continue
        return total

    def query(self, query_text: str, n_results: int = 5) -> list[dict]:
        col = self._get_collection()
        if not col or col.count() == 0:
            return []
        try:
            results = col.query(query_texts=[query_text], n_results=n_results)
        except Exception:
            return []
        output = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        for doc, meta, dist in zip(docs, metas, distances):
            output.append({
                "content": doc,
                "source": meta.get("source", ""),
                "chunk": meta.get("chunk", 0),
                "score": 1 - dist if dist <= 1 else 0,
            })
        return output

    def count(self) -> int:
        col = self._get_collection()
        return col.count() if col else 0

    def clear(self):
        col = self._get_collection()
        if col:
            self._client.delete_collection(self.collection_name)
            self._col = None
