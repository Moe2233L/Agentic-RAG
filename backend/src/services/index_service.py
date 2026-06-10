from pathlib import Path

from backend.src.rag.loader import DocumentLoader
from backend.src.rag.embedder import embedder
from backend.src.rag.store import vector_store
from backend.src.utils.helpers import get_logger

logger = get_logger(__name__)

from backend.src.constants import SUPPORTED_EXTENSIONS as _SUPPORTED


def index_kb(kb_id: str, dd: str) -> dict:
    chunks = DocumentLoader().load_directory(dd)
    if not chunks:
        raise ValueError("文档解析结果为空")
    texts = [c.text for c in chunks]
    sources = [c.metadata.get("source", "unknown") for c in chunks]
    dv = embedder.embed_dense(texts)
    vector_store.load()
    vector_store.insert(texts, sources, dv)
    # 检查被跳过的文件
    indexed_sources = set(sources)
    all_files = [f for f in Path(dd).iterdir() if f.is_file()]
    skipped = [f.name for f in all_files if f.name not in indexed_sources]
    failed = [f.name for f in all_files if f.name not in indexed_sources and f.suffix.lower() in _SUPPORTED]
    r = {"indexed": len(texts), "total": vector_store.count(), "sources": list(indexed_sources)}
    if failed:
        r["failed"] = failed
    if skipped:
        r["skipped"] = [f.name for f in all_files if f.name not in indexed_sources and f.suffix.lower() not in _SUPPORTED]
    return r
