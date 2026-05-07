import uuid
from langchain_core.messages import HumanMessage

from graph import build_graph


def run_chat():

    print("\n🌤️ LangGraph + LangChain Weather Agent ")
    print()

    graph = build_graph()

    thread_id = str(uuid.uuid4())

    while True:

        query = input("Query: ").strip()

        if query.lower() in ["quit", "exit"]:
            break

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        print("\n Running agent...\n")
        result = graph.invoke(
            {
                "messages": [{"role": "user", "content": query}],
                "question": query,
                "answer": "",
            },
            config=config,
        )

        print("\n Final Answer:\n")
        print(result["answer"])
        print("\n" + "=" * 50)

if __name__ == "__main__":
    run_chat()