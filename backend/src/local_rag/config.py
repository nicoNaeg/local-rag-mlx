from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAG_")

    qdrant_url: str = "http://localhost:6333"
    collection: str = "solencia_docs"
    embedding_model: str = "BAAI/bge-m3"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    device: str = "mps"
    embed_batch_size: int = 8
    rerank_candidates: int = 20
    top_k: int = 5
    corpus_dir: Path = Path("../data/corpus")
    eval_dir: Path = Path("eval")
