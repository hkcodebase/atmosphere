from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from config import settings
from db import get_embeddings, get_raw_driver

_PROMPT = ChatPromptTemplate.from_template("""You are a helpful assistant. Answer the question based ONLY on the provided context.
If the context doesn't contain enough information, say so — do not make things up.

Context:
{context}

Question: {question}

Answer:""")


def _get_llm() -> ChatOpenAI:
    # Docker Model Runner exposes an OpenAI-compatible API at this endpoint.
    # The model name must match the one declared in docker-compose.yml (provider.options.model).
    return ChatOpenAI(
        base_url=settings.llm_base_url,
        api_key="not-required",
        model=settings.llm_model,
        temperature=0.2,
        max_tokens=1024,
    )


def similarity_search(query: str, top_k: int = 5) -> list[dict]:
    embeddings = get_embeddings()
    query_vector = embeddings.embed_query(query)

    driver = get_raw_driver()
    with driver.session() as session:
        results = session.run(
            """
            CALL db.index.vector.queryNodes('document_chunks', $top_k, $vector)
            YIELD node AS chunk, score
            MATCH (d:Document)-[:HAS_CHUNK]->(chunk)
            RETURN chunk.text AS text,
                   chunk.source AS source,
                   chunk.page AS page,
                   d.name AS document,
                   score
            ORDER BY score DESC
            """,
            top_k=top_k,
            vector=query_vector,
        )
        hits = [dict(r) for r in results]
    driver.close()
    return hits


def rag_query(question: str, top_k: int = 5) -> dict:
    hits = similarity_search(question, top_k=top_k)
    context = "\n\n---\n\n".join(h["text"] for h in hits)

    llm = _get_llm()
    chain = (
        {"context": lambda _: context, "question": RunnablePassthrough()}
        | _PROMPT
        | llm
        | StrOutputParser()
    )
    answer = chain.invoke(question)
    return {"answer": answer, "sources": hits}
