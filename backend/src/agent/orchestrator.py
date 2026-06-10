import json

from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from backend.src.config import settings
from backend.src.rag.retriever import retriever
from backend.src.services.graph_service import graph as gs
from backend.src.utils.helpers import get_llm, get_logger

logger = get_logger(__name__)
llm = get_llm()

_TOOLS: dict[str, str] = {"vector": "语义向量检索(找相似文档)", "graph": "知识图谱查询(找实体关系)"}
if settings.tavily_api_key and settings.tavily_api_key != "tvly-xxx":
    _TOOLS["web"] = "网络搜索(最新信息)"
    logger.info("Tavily 已配置, web 工具可用")
else:
    logger.warning("Tavily 未配置, web 工具已禁用")


class State(TypedDict):
    q: str
    routes: list[str]
    idx: int
    ev: list[dict]
    use_web: bool


def route(state: State) -> dict:
    av = {k:v for k,v in _TOOLS.items() if k != 'web' or state.get('use_web', True)}
    if not av: av = {'vector': _TOOLS['vector']}
    tl = ', '.join(av.keys())
    r = llm.invoke(f"判断问题需要哪些检索工具。\n可选工具: {', '.join(f'{k}({v})' for k,v in av.items())}\n规则:\n- 信息求证类 → vector\n- 实体关系类 → graph\n- 实时/外网信息 → web\n- 多需求可返回多个\n- 只输出 JSON 数组，如 [\"vector\", \"web\"]\n问题: {state['q']}")
    try:
        rt = json.loads(r.content.strip().removeprefix("```json").removesuffix("```").strip())
        rt = [t for t in rt if t in _TOOLS] or ["vector"]
    except Exception:
        rt = ["vector"]
    logger.info(f"Agent routes: {rt}")
    return {"routes": rt, "idx": 0}


def run(state: State) -> dict:
    idx = state["idx"]
    t = state["routes"][idx]
    logger.info(f"Executing: {t} ({idx+1}/{len(state['routes'])})")
    ev = []
    try:
        if t == "vector":
            ev = retriever.retrieve(state["q"])
        elif t == "graph":
            try: gs._connect()
            except: logger.warning("Neo4j 不可用"); return {"ev": state["ev"], "idx": idx + 1}
            ev = gs.search(state["q"])
        elif t == "web":
            from tavily import TavilyClient
            r = TavilyClient(api_key=settings.tavily_api_key).search(query=state["q"], search_depth="basic", max_results=3)
            ev = [
                {"id": f"web_{i}", 
                "text": x.get("content", ""), 
                "source": x.get("url", ""), 
                "score": x.get("score", 0)
                } 
                for i, x in enumerate(r.get("results", []))]
        return {"ev": state["ev"] + ev, "idx": idx + 1}
    except Exception as e:
        logger.warning(f"{t} fail: {e}")
        return {"ev": state["ev"], "idx": idx + 1}


def next(state: State) -> str:
    return "run" if state["idx"] + 1 < len(state["routes"]) else "end"


def build():
    g = StateGraph(State)
    g.add_node("route", route)
    g.add_node("run", run)
    g.add_node("end", lambda s: {})
    g.set_entry_point("route")
    g.add_edge("route", "run")
    g.add_conditional_edges("run", next, {"run": "run", "end": "end"})
    g.add_edge("end", END)
    return g.compile()


agent = build()
