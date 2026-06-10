import base64, json
from pathlib import Path

from langchain_core.messages import HumanMessage

from backend.src.utils.helpers import get_llm, get_logger

logger = get_logger(__name__)

# 图片后缀 → MIME 映射
_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}
_IMAGE_MIME = {
    ex.lstrip("."): "image/jpeg" if ex in (".jpg", ".jpeg") else f"image/{ex.lstrip('.')}"
    for ex in _IMAGE_SUFFIXES
}
_IMAGE_MIME["jpg"] = "image/jpeg"


class RelationExtractor:
    def __init__(self):
        self._llm = get_llm()

    def __call__(self, text: str) -> list[dict]:
        """从文本提取实体关系"""
        try:
            r = self._llm.invoke(f"从以下文本提取实体关系三元组。要求:1.抽取5-8条核心关系 2.并列概念拆为独立实体(\"A、B、C\"→A,B,C) 3.关系用具体动词(属于/包含/负责/位于/规定) 4.只输出JSON数组[{{'subject':str,'relation':str,'object':str}}],无则返回[]:\n{text}")
            return json.loads(r.content.strip().removeprefix("```json").removesuffix("```").strip())
        except Exception as e:
            logger.warning(f"LLM 抽取失败: {e}")
            return []

    def extract_from_image(self, fp: str | Path) -> list[dict]:
        """从图片提取实体关系（优先 VLM，失败则 OCR 兜底）"""
        p = Path(fp)
        # VLM
        try:
            mt = _IMAGE_MIME.get(p.suffix.lower().lstrip("."), "image/jpeg")
            b64 = base64.b64encode(p.read_bytes()).decode()
            msg = HumanMessage(content=[
                {"type": "text", "text": "从这张图片中提取实体关系三元组。要求:1.抽取5-8条核心关系 2.关系用具体动词 3.只输出JSON数组[{'subject':str,'relation':str,'object':str}],无则返回[]"},
                {"type": "image_url", "image_url": {"url": f"data:{mt};base64,{b64}"}},
            ])
            r = self._llm.invoke([msg])
            txt = r.content.strip().removeprefix("```json").removesuffix("```").strip()
            result = json.loads(txt)
            if result:
                logger.info(f"VLM 识别成功: {p.name}")
                return result
        except Exception as e:
            logger.warning(f"VLM 失败，尝试 OCR: {e}")
        # OCR 兜底
        try:
            from backend.src.rag.loader import DocumentLoader
            chunks = DocumentLoader().load(str(p))
            if chunks:
                text = chunks[0].text
                logger.info(f"OCR 提取文本: {len(text)} chars")
                return self.__call__(text)
        except Exception as e2:
            logger.warning(f"OCR 也失败: {e2}")
        return []


extractor = RelationExtractor()
