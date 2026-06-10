from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    conversation_id: str | None = None
    use_web: bool = False
    deep_mode: bool = False


class CreateKBRequest(BaseModel):
    name: str
    description: str = ""
