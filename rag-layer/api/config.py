from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "rag_password"
    llm_base_url: str = "http://model-runner.docker.internal/engines/llama.cpp/v1"
    llm_model: str = "ai/gemma3:4B-Q4_K_M"
    embed_model: str = "all-MiniLM-L6-v2"
    docs_path: str = "./docs"
    chunk_size: int = 1000
    chunk_overlap: int = 200

    class Config:
        env_file = ".env"


settings = Settings()
