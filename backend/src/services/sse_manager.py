import json


class SSEManager:
    def __init__(self):
        self._sid = ""

    def start(self, sid: str):
        self._sid = sid
        return {"event": "start", "data": json.dumps({"conversation_id": sid})}

    def token(self, t: str) -> dict:
        return {"event": "token", "data": json.dumps({"token": t})}

    def done(self, answer: str, evidence: list[dict]) -> dict:
        return {"event": "done", "data": json.dumps({"answer": answer, "conversation_id": self._sid, "evidence": evidence})}

    def status(self, msg: str) -> dict:
        return {"event": "status", "data": json.dumps({"status": msg})}

    def error(self, msg: str) -> dict:
        return {"event": "error", "data": json.dumps({"error": msg})}


sse = SSEManager()
