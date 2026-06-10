import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from httpx import Client
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from sse_starlette.sse import EventSourceResponse

from backend.src.config import settings
from backend.src.models import CreateKBRequest, QueryRequest
from backend.src.rag.retriever import retriever
from backend.src.services import kb_service
from backend.src.services.index_service import index_kb
from backend.src.services.sse_manager import sse
from backend.src.utils.helpers import get_logger

logger = get_logger(__name__)
sessions: dict[str, list[dict]] = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
    import asyncio
    from backend.src.rag.embedder import embedder
    asyncio.create_task(asyncio.to_thread(embedder.warmup))
    logger.info(f"启动 {settings.host}:{settings.port}")
    yield
    from backend.src.services.graph_service import close_graph
    await close_graph()


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query")
async def query(req: QueryRequest):
    sid = req.conversation_id or str(uuid4())
    ev = await _retrieve(req.question, req.use_web, req.deep_mode)
    ans = _generate(req.question, ev)
    sessions.setdefault(sid, []).append({"q": req.question, "a": ans, "ev": ev})
    return {"answer": ans, "conversation_id": sid, "evidence": ev}


@app.post("/query/stream")
async def query_stream(req: QueryRequest, request: Request):
    sid = req.conversation_id or str(uuid4())

    async def gen():
        if await request.is_disconnected():
            return
        yield sse.start(sid)
        # 构建对话历史
        prev = sessions.get(sid, [])
        history = "\n".join(f"{'用户' if s['q'] else '助手'}: {s.get('q') or s.get('a','')[:100]}" for s in prev[-4:])
        yield sse.status("检索中…")
        ev = await _retrieve(req.question, req.use_web, req.deep_mode, history)
        yield sse.status("生成回答…")
        llm, msg = _build_llm(True), _build_msg(req.question, ev, history)
        ans = ""
        try:
            async for c in llm.astream(msg):
                if await request.is_disconnected():
                    break
                if t := c.content or "":
                    ans += t
                    yield sse.token(t)
        except Exception as e:
            logger.error(f"stream fail: {e}")
            yield sse.error(str(e))
            ans = f"生成失败: {e}"
        sessions.setdefault(sid, []).append({"q": req.question, "a": ans, "ev": ev})
        yield sse.done(ans, ev)

    return EventSourceResponse(gen())


def _web_search(q: str) -> list[dict]:
    from tavily import TavilyClient
    try:
        r = TavilyClient(api_key=settings.tavily_api_key).search(query=q, search_depth="basic", max_results=3)
    except Exception as e:
        logger.warning(f"联网搜索失败（降级为本地检索）: {e}")
        return []
    return [{"id": f"web_{i}", "text": x.get("content", ""), "source": x.get("url", ""), "score": x.get("score", 0)} for i, x in enumerate(r.get("results", []))]

async def _retrieve(q: str, use_web: bool = True, deep_mode: bool = False, history: str = "") -> list[dict]:
    import asyncio
    def _sync():
        if deep_mode:
            from backend.src.agent.orchestrator import agent
            try:
                return agent.invoke({"q": q, "routes": [], "idx": 0, "ev": [], "use_web": use_web}).get("ev", [])
            except Exception as e:
                logger.warning(f"agent fail: {e}")
        from concurrent.futures import ThreadPoolExecutor, as_completed
        tasks, ev = {"vector": lambda: retriever.retrieve(q)}, []
        if use_web and settings.tavily_api_key:
            tasks["web"] = lambda: _web_search(q)
        with ThreadPoolExecutor(max_workers=len(tasks)) as pool:
            for f in as_completed([pool.submit(t) for t in tasks.values()]):
                try:
                    ev.extend(f.result())
                except Exception as e:
                    logger.warning(f"retrieve fail: {e}")
        return ev
    return await asyncio.to_thread(_sync)


def _build_msg(q: str, ev: list[dict], history: str = "") -> list:
    sp = (
        '你是一个知识库问答助手。严格按以下规则回答：\n'
        '1. 严格依据参考资料回答，禁止使用自身知识。资料中没有则直接说"参考资料中未提及"\n'
        '2. 回答要简洁清晰，复杂信息用分点列出\n'
        '3. 不要编造信息，不确定就说"无法确定"'
    )
    user_q = q
    if history:
        sp = f"对话历史:\n{history}\n\n当前问题: {q}\n\n" + sp
        user_q = f"根据对话历史，回答: {q}"
    if ev:
        sp += "\n\n参考资料:\n" + "\n\n".join(f"[{i+1}] {e['source']}\n{e['text']}" for i, e in enumerate(ev))
    return [SystemMessage(content=sp), HumanMessage(content=user_q)]


def _build_llm(streaming: bool = False):
    from backend.src.utils.helpers import get_llm
    llm = get_llm(temperature=0.3)
    if streaming:
        llm = ChatOpenAI(model=settings.llm_model, openai_api_key=settings.openai_api_key, openai_api_base=settings.openai_api_base, temperature=0.3, streaming=True, http_client=Client(proxy=None))
    return llm


def _generate(q: str, ev: list[dict]) -> str:
    try:
        return _build_llm().invoke(_build_msg(q, ev)).content
    except Exception as e:
        return f"生成失败: {e}"


# ── Knowledge Base API ─────────────────────────────────────────


@app.post("/knowledge-bases")
def create_kb(req: CreateKBRequest):
    return kb_service.create(req.name, req.description)


@app.get("/knowledge-bases")
def list_kbs():
    return {"knowledge_bases": kb_service.list_all()}


@app.delete("/knowledge-bases/{kb_id}")
def delete_kb(kb_id: str):
    if not kb_service.delete(kb_id):
        raise HTTPException(404, "知识库不存在")
    return {"deleted": kb_id}


@app.post("/knowledge-bases/{kb_id}/upload")
async def upload_kb(kb_id: str, files: list[UploadFile] = File(...)):
    if not kb_service.get(kb_id):
        raise HTTPException(404, "知识库不存在")
    dd = kb_service.docs_dir(kb_id); dd.mkdir(parents=True, exist_ok=True)
    saved, rejected = [], []
    for f in files:
        ext = Path(f.filename or "").suffix.lower()
        if ext not in kb_service.SUPPORTED:
            rejected.append({"filename": f.filename, "reason": f"不支持 {ext}"})
            continue
        dest = dd / f.filename
        with open(dest, "wb") as out:
            shutil.copyfileobj(f.file, out)
        saved.append({"filename": f.filename, "size": dest.stat().st_size})
    return {"saved": saved, "rejected": rejected}


@app.get("/knowledge-bases/{kb_id}/documents")
def list_docs(kb_id: str):
    if not kb_service.get(kb_id):
        raise HTTPException(404, "知识库不存在")
    dd = kb_service.docs_dir(kb_id)
    docs = [{"filename": f.name, "size": f.stat().st_size, "suffix": f.suffix.lower()} for f in sorted(dd.iterdir()) if f.is_file()] if dd.exists() else []
    # 查已索引的源文件
    idxd: set[str] = set()
    try:
        from backend.src.rag.store import vector_store
        vector_store.load()
        all_meta = vector_store._col.get(include=["metadatas"])
        if all_meta and all_meta["metadatas"]:
            idxd = set(m.get("source", "") for m in all_meta["metadatas"] if m.get("source"))
    except Exception:
        pass
    for d in docs:
        d["indexed"] = d["filename"] in idxd
    return {"documents": docs, "total": len(docs)}


@app.delete("/knowledge-bases/{kb_id}/documents/{filename:path}")
def delete_doc(kb_id: str, filename: str):
    if not kb_service.get(kb_id):
        raise HTTPException(404, "知识库不存在")
    target = kb_service.docs_dir(kb_id) / filename
    if not target.exists() or not target.is_file():
        raise HTTPException(404, "文件不存在")
    target.unlink()
    return {"deleted": filename}


@app.post("/knowledge-bases/{kb_id}/index")
async def index_kb_endpoint(kb_id: str):
    if not kb_service.get(kb_id):
        raise HTTPException(404, "知识库不存在")
    dd = kb_service.docs_dir(kb_id); dd.mkdir(parents=True, exist_ok=True)
    if not any(dd.iterdir()):
        raise HTTPException(400, "知识库中没有文档")
    try:
        return index_kb(kb_id, str(dd))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"索引失败: {e}")
        raise HTTPException(500, f"索引失败: {e}")


@app.get("/knowledge-bases/{kb_id}/graph")
def get_graph(kb_id: str):
    if not kb_service.get(kb_id):
        raise HTTPException(404, "知识库不存在")
    return kb_service.load_graph(kb_id)


@app.delete("/knowledge-bases/{kb_id}/graph")
def delete_graph(kb_id: str):
    if not kb_service.get(kb_id):
        raise HTTPException(404, "知识库不存在")
    kb_service.save_graph(kb_id, {"nodes": [], "edges": []})
    return {"deleted": True}


@app.post("/knowledge-bases/{kb_id}/graph/build")
async def build_graph(kb_id: str):
    if not kb_service.get(kb_id):
        raise HTTPException(404, "知识库不存在")
    dd = kb_service.docs_dir(kb_id); dd.mkdir(parents=True, exist_ok=True)
    if not any(dd.iterdir()):
        raise HTTPException(400, "知识库中没有文档")
    try:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from backend.src.rag.loader import DocumentLoader
        from backend.src.tools.extraction_tool import extractor
        from backend.src.services.graph_service import graph

        from pathlib import Path as _P
        img_ext = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}
        img_files = [f for f in _P(dd).iterdir() if f.suffix.lower() in img_ext]
        txt_files = [f for f in _P(dd).iterdir() if f.suffix.lower() not in img_ext and f.is_file()]

        chunks = []
        for f in txt_files:
            try: chunks.extend(DocumentLoader(chunk_size=4096).load(str(f)))
            except Exception as e: logger.warning(f"{f.name}: {e}")
        if not chunks and not img_files:
            raise HTTPException(400, "文档解析结果为空")
        all_nodes, all_edges, sn, se = [], [], set(), set()

        def process(t: str) -> dict:
            rels = extractor(t)
            ents: dict[str, int] = {}
            for r in rels:
                for k in ["subject", "object"]:
                    if r[k] not in ents:
                        ents[r[k]] = abs(hash(r[k])) % 10 + 1
            nodes_list = [{"id": k, "group": v} for k, v in ents.items()]
            rels_list = [{"source": r["subject"], "target": r["object"], "label": r["relation"]} for r in rels]
            # 无关系时加少量共现边兜底
            if not rels_list and len(ents) >= 2:
                ids = list(ents.keys())
                rels_list = [{"source": ids[i], "target": ids[i+1], "label": "相关"} for i in range(min(3, len(ids)-1))]
            return {"entities": nodes_list, "relations": rels_list}

        with ThreadPoolExecutor(max_workers=2) as pool:
            for f in as_completed([pool.submit(process, c.text) for c in chunks]):
                d = f.result()
                for n in d["entities"]:
                    if n["id"] not in sn:
                        sn.add(n["id"]); all_nodes.append(n)
                for e in d["relations"]:
                    k = (e["source"], e["target"])
                    if k not in se:
                        se.add(k); all_edges.append(e)
        # 图片文件直接用 VLM 抽取
        for img_f in img_files:
            try:
                rels = extractor.extract_from_image(str(img_f))
                for r in rels:
                    for k in ["subject", "object"]:
                        if r[k] not in sn:
                            sn.add(r[k]); all_nodes.append({"id": r[k], "group": abs(hash(r[k])) % 10 + 1})
                    ek = (r["subject"], r["target"])
                    if ek not in se:
                        se.add(ek); all_edges.append({"source": r["subject"], "target": r["object"], "label": r["relation"]})
            except Exception as e:
                logger.warning(f"图片 {img_f.name} 抽取失败: {e}")
        kb_service.save_graph(kb_id, {"nodes": all_nodes, "edges": all_edges})
        try: graph.delete(kb_id); graph.save(kb_id, all_nodes, all_edges)
        except Exception: logger.warning("Neo4j 不可用，跳过")
        # 实体向量化
        if all_nodes:
            try:
                from backend.src.rag.embedder import embedder
                from backend.src.rag.store import vector_store
                entity_texts = [n["id"] for n in all_nodes]
                entity_dv = embedder.embed_dense(entity_texts)
                vector_store.load()
                # 删旧实体向量
                exist = vector_store._col.get(where={"$and": [{"type": "entity"}, {"kb_id": kb_id}]})
                if exist and exist["ids"]:
                    vector_store._col.delete(ids=exist["ids"])
                # 写新实体向量
                eids = [f"ent_{kb_id}_{i}" for i in range(len(entity_texts))]
                emeta = [{"source": n["id"], "type": "entity", "kb_id": kb_id} for n in all_nodes]
                vector_store._col.add(ids=eids, embeddings=entity_dv.tolist(), documents=entity_texts, metadatas=emeta)
                logger.info(f"实体向量化完成: {len(entity_texts)} 个")
            except Exception as e:
                logger.warning(f"实体向量化失败: {e}")
        return {"chunks": len(chunks), "entities": len(all_nodes), "relations": len(all_edges)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"图谱构建失败: {e}")
        raise HTTPException(500, f"图谱构建失败: {e}")


@app.get("/knowledge-bases/index/status")
def index_status():
    try:
        from backend.src.rag.store import vector_store
        vector_store.load()
        return {"total": vector_store.count()}
    except Exception:
        return {"total": 0}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.src.main:app", host=settings.host, port=settings.port)
