from functools import lru_cache
from neo4j import GraphDatabase
from langchain_neo4j import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from sentence_transformers import SentenceTransformer
from langchain_core.embeddings import Embeddings
from config import settings


class LocalEmbeddings(Embeddings):
    """Wraps sentence-transformers for LangChain compatibility."""

    def __init__(self, model_name: str):
        self._model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, show_progress_bar=False).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self._model.encode(text, show_progress_bar=False).tolist()


@lru_cache(maxsize=1)
def get_embeddings() -> LocalEmbeddings:
    return LocalEmbeddings(settings.embed_model)


def get_graph() -> Neo4jGraph:
    return Neo4jGraph(
        url=settings.neo4j_uri,
        username=settings.neo4j_user,
        password=settings.neo4j_password,
    )


def get_raw_driver():
    return GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )


def get_vector_store() -> Neo4jVector:
    return Neo4jVector(
        embedding=get_embeddings(),
        url=settings.neo4j_uri,
        username=settings.neo4j_user,
        password=settings.neo4j_password,
        index_name="document_chunks",
        node_label="Chunk",
        text_node_property="text",
        embedding_node_property="embedding",
    )


def init_schema() -> None:
    driver = get_raw_driver()
    with driver.session() as session:
        session.run("""
            CREATE CONSTRAINT chunk_id IF NOT EXISTS
            FOR (c:Chunk) REQUIRE c.id IS UNIQUE
        """)
        session.run("""
            CREATE CONSTRAINT document_id IF NOT EXISTS
            FOR (d:Document) REQUIRE d.id IS UNIQUE
        """)
        # embedding dim for all-MiniLM-L6-v2 is 384
        session.run("""
            CREATE VECTOR INDEX document_chunks IF NOT EXISTS
            FOR (c:Chunk) ON (c.embedding)
            OPTIONS {indexConfig: {
                `vector.dimensions`: 384,
                `vector.similarity_function`: 'cosine'
            }}
        """)
    driver.close()
