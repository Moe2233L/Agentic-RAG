import numpy as np
from numpy import ndarray

from backend.src.config import settings
from backend.src.utils.helpers import get_logger, get_device

logger = get_logger(__name__)


class BGEEmbeddingFunction:
    def __init__(self, model_path: str | None = None):
        self.model_path = model_path or settings.bge_model_path
        self._model = None

    def warmup(self):
        """启动时预加载模型"""
        logger.info("预加载 BGE-M3 嵌入模型…")
        self._load()
        logger.info("BGE-M3 模型已就绪")

    def _load(self):
        if self._model:
            return
        import os
        os.environ["HF_HUB_OFFLINE"] = "1"
        from FlagEmbedding import BGEM3FlagModel
        self._model = BGEM3FlagModel(self.model_path, use_fp16=True, device=get_device())

    def embed_dense(self, texts: list[str]) -> ndarray:
        self._load()
        return np.array(self._model.encode(texts, batch_size=32)["dense_vecs"], dtype=np.float32)

    def embed_query(self, text: str) -> tuple[ndarray, dict[int, float]]:
        self._load()
        out = self._model.encode([text], batch_size=1, return_sparse=True)
        return np.array(out["dense_vecs"][0], dtype=np.float32), {int(t): float(w) for t, w in out["lexical_weights"][0].items()}


embedder = BGEEmbeddingFunction()
