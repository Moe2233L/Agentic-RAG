from backend.src.config import settings
from backend.src.rag.embedder import embedder
from backend.src.rag.store import vector_store
from backend.src.utils.helpers import get_device, get_logger

logger = get_logger(__name__)

_reranker = None

def _get_reranker():
    global _reranker
    if _reranker is None:
        from FlagEmbedding import FlagReranker
        _reranker = FlagReranker(settings.bge_reranker_path, use_fp16=True, device=get_device())
        logger.info("Reranker 模型已加载")
    return _reranker


class Retriever:
    def __init__(self, top_k: int = 10, rerank_top_k: int = 5):
        self.top_k = top_k
        self.rerank_top_k = rerank_top_k

    def retrieve(self, q: str) -> list[dict]:
        dv, _ = embedder.embed_query(q)
        # 文档检索
        r = vector_store.search_dense(dv, self.top_k * 2, filter_={"type": {"$ne": "entity"}})
        # 实体检索（找 top 3 最相关实体）
        try:
            er = vector_store.search_dense(dv, 3, filter_={"type": "entity"})
            for e in er:
                e["source"] = f"实体: {e['source']}"
                e["text"] = f"【实体】{e['text']}"
            r = er + r
        except Exception as e:
            logger.warning(f"Entity search fail: {e}")
        # 去重（按文本相似度去重，保留来源不同的记录）
        seen: set[str] = set()
        deduped = []
        for item in r:
            key = item.get("text", "")[:60]
            if key not in seen:
                seen.add(key)
                deduped.append(item)
        if len(deduped) < len(r):
            logger.info(f"去重: {len(r)} → {len(deduped)}")
        return self._rerank(q, deduped)

    def _rerank(self, q: str, cand: list[dict]) -> list[dict]:
        if not cand:
            return []
        try:
            rr = _get_reranker()
            sc = sorted(zip(cand, rr.compute_score([(q, c["text"]) for c in cand], normalize=True)), key=lambda x: x[1], reverse=True)[:self.rerank_top_k]
            return [{"id": it.get("id", ""), "text": it["text"], "source": it.get("source", ""), "score": float(s)} for it, s in sc]
        except Exception as e:
            logger.warning(f"Rerank fail, fallback: {e}")
            return cand[:self.rerank_top_k]


retriever = Retriever()
