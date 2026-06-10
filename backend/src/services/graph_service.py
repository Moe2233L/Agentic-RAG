from typing import Any

from backend.src.config import settings
from backend.src.utils.helpers import get_logger

logger = get_logger(__name__)


class GraphService:
    def __init__(self):
        self._driver = None

    def _connect(self):
        if self._driver:
            return
        from neo4j import GraphDatabase
        self._driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        self._driver.verify_connectivity()

    def save(self, kb_id: str, nodes: list[dict], edges: list[dict]):
        if not nodes and not edges:
            return
        self._connect()
        with self._driver.session() as s:
            if nodes:
                s.run("UNWIND $ns AS n MERGE (e:Entity {text: n.id, kb_id: $kb}) SET e.label = n.label, e.group = n.group", ns=nodes, kb=kb_id)
            if edges:
                es = [{"src": e["source"], "dst": e["target"], "lbl": e.get("label", "")} for e in edges]
                s.run("UNWIND $es AS e MATCH (a:Entity {text: e.src, kb_id: $kb}) MATCH (b:Entity {text: e.dst, kb_id: $kb}) MERGE (a)-[r:RELATION {type: e.lbl, kb_id: $kb}]->(b)", es=es, kb=kb_id)

    def search(self, q: str, k: int = 10) -> list[dict]:
        self._connect()
        cypher = self._to_cypher(q)
        try:
            with self._driver.session() as s:
                return [self._fmt(r) for r in s.run(cypher)[:k]]
        except Exception as e:
            logger.warning(f"Cypher fail: {e}")
            return []

    def search_entity(self, entity: str, hops: int = 2) -> list[dict]:
        self._connect()
        c = f"MATCH path = (s:Entity {{text: $e}})-[*1..{hops}]-(o) RETURN [n in nodes(path) | n.text] AS nodes, [r in relationships(path) | r.type] AS rels LIMIT 20"
        try:
            with self._driver.session() as s:
                return [{"path": " → ".join(r["nodes"]), "rels": r["rels"]} for r in s.run(c, e=entity)]
        except Exception as e:
            logger.warning(f"Hop fail: {e}")
            return []

    @staticmethod
    def _to_cypher(q: str) -> str:
        ql = q.lower()
        if any(w in ql for w in ["所有", "全部", "列出"]):
            return "MATCH (n:Entity) RETURN n.text, n.label LIMIT 50"
        if any(w in ql for w in ["关系", "关联", "连接"]):
            return "MATCH (a)-[r:RELATION]->(b) RETURN a.text, r.type, b.text LIMIT 50"
        return "MATCH (n) OPTIONAL MATCH (n)-[r]->(m) RETURN n.text, n.label, r.type, m.text LIMIT 50"

    @staticmethod
    def _fmt(r: Any) -> dict:
        return {k: r[k] for k in r.keys() if r[k] is not None}

    def delete(self, kb_id: str):
        self._connect()
        with self._driver.session() as s:
            s.run("MATCH (e:Entity {kb_id: $kb}) DETACH DELETE e", kb=kb_id)

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None


graph = GraphService()


# app 关闭时自动释放 Neo4j 连接
async def close_graph():
    graph.close()
