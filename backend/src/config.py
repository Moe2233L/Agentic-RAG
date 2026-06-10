from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_api_base: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    bge_model_path: str = "BAAI/bge-m3"
    bge_reranker_path: str = "BAAI/bge-reranker-v2-m3"
    chroma_collection: str = "agentic_rag"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    tavily_api_key: str = ""

    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
