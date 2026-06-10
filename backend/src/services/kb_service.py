import json, shutil, uuid
from datetime import datetime
from pathlib import Path

KB_ROOT = Path("data/knowledge_bases")
KB_ROOT.mkdir(parents=True, exist_ok=True)
META = KB_ROOT / "_meta.json"
from backend.src.constants import SUPPORTED_EXTENSIONS as SUPPORTED


def _load() -> list[dict]:
    return json.loads(META.read_text("utf-8")) if META.exists() else []


def _save(kbs: list[dict]):
    META.write_text(json.dumps(kbs, ensure_ascii=False, indent=2), "utf-8")


def create(name: str, desc: str = "") -> dict:
    kb = {"id": uuid.uuid4().hex[:12], "name": name, "description": desc, "created_at": datetime.now().isoformat()}
    kbs = _load(); kbs.append(kb); _save(kbs)
    (KB_ROOT / kb["id"] / "documents").mkdir(parents=True)
    (KB_ROOT / kb["id"] / "graph.json").write_text('{"nodes":[],"edges":[]}', "utf-8")
    return kb


def list_all() -> list[dict]:
    return _load()


def get(kb_id: str) -> dict | None:
    return next((kb for kb in _load() if kb["id"] == kb_id), None)


def delete(kb_id: str) -> bool:
    kbs = _load(); new = [kb for kb in kbs if kb["id"] != kb_id]
    if len(new) == len(kbs): return False
    _save(new); shutil.rmtree(KB_ROOT / kb_id, ignore_errors=True); return True


def docs_dir(kb_id: str) -> Path:
    return KB_ROOT / kb_id / "documents"


def graph_path(kb_id: str) -> Path:
    return KB_ROOT / kb_id / "graph.json"


def load_graph(kb_id: str) -> dict:
    p = graph_path(kb_id)
    return json.loads(p.read_text("utf-8")) if p.exists() else {"nodes": [], "edges": []}


def save_graph(kb_id: str, data: dict):
    graph_path(kb_id).write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
