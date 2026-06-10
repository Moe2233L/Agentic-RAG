from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.src.utils.helpers import get_logger, normalize_whitespace

logger = get_logger(__name__)

from backend.src.constants import SUPPORTED_EXTENSIONS as _SUPPORTED


class DocumentChunk:
    def __init__(self, text: str, metadata: dict | None = None):
        self.text = text
        self.metadata = metadata or {}


class DocumentLoader:
    def __init__(self, chunk_size: int = 512):
        self.chunk_size = chunk_size

    def load(self, fp: str | Path) -> list[DocumentChunk]:
        p = Path(fp)
        chunks = self._semantic_chunk(self._extract_text(p))
        return [DocumentChunk(t, {"source": p.name, "chunk_index": i, "total_chunks": len(chunks)}) for i, t in enumerate(chunks)]

    def load_directory(self, dp: str | Path, max_workers: int = 4) -> list[DocumentChunk]:
        files = [f for f in Path(dp).iterdir() if f.suffix.lower() in _SUPPORTED]
        if len(files) <= 1:
            return self.load(files[0]) if files else []
        from concurrent.futures import ThreadPoolExecutor, as_completed
        r: list[DocumentChunk] = []
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            fut = {ex.submit(self.load, f): f for f in files}
            for f in as_completed(fut):
                try:
                    r.extend(f.result())
                except Exception as e:
                    logger.warning(f"{fut[f].name}: {e}")
        return r

    def _extract_text(self, p: Path) -> str:
        if p.suffix.lower() in {".txt", ".md"}:
            return normalize_whitespace(p.read_text("utf-8", errors="ignore"))
        # 图片优先走 VLM
        img_ext = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}
        if p.suffix.lower() in img_ext:
            try:
                import base64, json
                from langchain_core.messages import HumanMessage
                from backend.src.utils.helpers import get_llm
                llm = get_llm()
                mime = {"png":"image/png","jpg":"image/jpeg","jpeg":"image/jpeg","tiff":"image/tiff","bmp":"image/bmp","webp":"image/webp"}
                b64 = base64.b64encode(p.read_bytes()).decode()
                msg = HumanMessage(content=[
                    {"type": "text", "text": "用中文详细描述这张图片中的内容，包括所有文字、数据、表格和关系。"},
                    {"type": "image_url", "image_url": {"url": f"data:{mime.get(p.suffix.lower().lstrip('.'),'image/jpeg')};base64,{b64}"}},
                ])
                r = llm.invoke([msg])
                txt = r.content.strip()
                if txt:
                    logger.info(f"VLM 描述成功: {p.name}")
                    return normalize_whitespace(txt)
            except Exception as e:
                logger.warning(f"VLM 描述失败，尝试 OCR: {e}")
        try:
            from unstructured.partition.auto import partition
            return normalize_whitespace("\n\n".join(str(e.text) for e in partition(str(p)) if hasattr(e, "text") and e.text))
        except ImportError:
            return normalize_whitespace(p.read_text("utf-8", errors="ignore"))
        except Exception as e:
            logger.error(f"{p.name}: {e}")
            return ""

    def _semantic_chunk(self, text: str) -> list[str]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=int(self.chunk_size * 0.1),
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", "；", ";", "，", ",", " ", ""],
            keep_separator=False,
        )
        return splitter.split_text(text)
