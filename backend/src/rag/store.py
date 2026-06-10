import json
from pathlib import Path

from numpy import ndarray

from backend.src.config import settings

CHROMA_DIR = Path("data/chroma")


class VectorStore:
    def __init__(self, name: str | None = None):
        self.name = name or settings.chroma_collection
        self._col = None

    def load(self):
        if self._col:
            return
        import chromadb
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        cli = chromadb.PersistentClient(path=str(CHROMA_DIR))
        try:
            self._col = cli.get_collection(self.name)
        except Exception:
            self._col = cli.create_collection(self.name, metadata={"hnsw:space": "ip"})

    def insert(self, texts: list[str], sources: list[str], dv: ndarray, tags: list[str] | None = None):
        self.load()
        ids = [f"{self.name}_{i}" for i in range(self.count(), self.count() + len(texts))]
        meta = [{"source": s} for s in sources]
        if tags:
            for i, t in enumerate(tags):
                if t:
                    meta[i]["tags"] = t
        self._col.add(ids=ids, embeddings=dv.tolist(), documents=texts, metadatas=meta)

    def search_dense(self, qv: ndarray, k: int = 10, filter_: dict | None = None) -> list[dict]:
        self.load()
        kw = {"query_embeddings": qv.tolist(), "n_results": k}
        if filter_:
            kw["where"] = filter_
        r = self._col.query(**kw)
        return [
                {"id": r["ids"][0][i], 
                "score": r["distances"][0][i], 
                "text": r["documents"][0][i], 
                "source": r["metadatas"][0][i].get("source", "")
                } 
                for i in range(len(r["ids"][0]))]

    def search_sparse(self, qs: dict[int, float], k: int = 10) -> list[dict]:
        self.load()
        d = self._col.get(include=["documents", "metadatas"])
        sc = sorted((sum(qs.get(t, 0) * w for t, w in json.loads(d["metadatas"][i].get("sv", "{}")).items()), d["documents"][i], d["metadatas"][i].get("source", ""), d["ids"][i]) for i in range(len(d["ids"])))
        return [{
                "id": i, 
                "score": s, 
                "text": t, 
                "source": c
                } 
                for s, t, c, i in sc[-k:]][::-1]

    def search_hybrid(self, qv: ndarray, qs: dict[int, float], k: int = 10) -> dict:
        return {"dense": self.search_dense(qv, k), "sparse": self.search_sparse(qs, k)}

    def count(self) -> int:
        self.load()
        return self._col.count()

    def delete_all(self):
        self.load()
        ids = self._col.get()["ids"]
        if ids:
            self._col.delete(ids=ids)


vector_store = VectorStore()
