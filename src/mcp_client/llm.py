import os
import json

from langchain_openai import ChatOpenAI

# Optional: boto3 is used for Bedrock integration
try:
    import boto3
except Exception:
    boto3 = None


class BedrockLLM:
    """Minimal Bedrock wrapper to provide a compatible interface for the codebase.

    This implementation uses the `bedrock-runtime` boto3 client (invoke_model).
    It returns a simple object with a `.content` attribute similar to LangChain Chat outputs.
    """

    def __init__(self, model_id: str, region_name: str = "us-east-1"):
        if boto3 is None:
            raise RuntimeError("boto3 is required for Bedrock backend but is not installed")
        self.model_id = model_id
        self.region_name = region_name
        self.client = boto3.client("bedrock-runtime", region_name=region_name)
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))

    def invoke(self, messages):
        # Build a prompt from incoming messages. The exact format can be adjusted.
        if isinstance(messages, list):
            prompt = "\n".join(getattr(m, "content", str(m)) for m in messages)
        else:
            prompt = str(messages)

        payload = {"input": prompt, "temperature": self.temperature}

        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload),
        )

        body = response.get("body")
        if hasattr(body, "read"):
            body = body.read()

        try:
            data = json.loads(body)
        except Exception:
            # Best-effort decode
            data = {"output": body.decode() if isinstance(body, (bytes, bytearray)) else str(body)}

        # Attempt to extract text from common keys
        text = None
        if isinstance(data, dict):
            text = data.get("output") or data.get("generatedText") or data.get("results")
            if isinstance(text, (list, dict)):
                text = json.dumps(text)
        if not text:
            text = str(data)

        class Message:
            def __init__(self, content):
                self.content = content

        return Message(text)


def get_llm():
    """Factory that returns either a local LLM (ChatOpenAI against a local OpenAI-compatible endpoint)
    or a Bedrock-backed LLM wrapper depending on the `LLM_BACKEND` environment variable.

    Environment:
      - LLM_BACKEND: 'local' or 'bedrock' (default: local)
      - DOCKER_MODEL_NAME / DOCKER_MODEL_URL: used for local backend
      - BEDROCK_MODEL_ID / AWS_REGION: used for Bedrock backend
    """
    backend = os.getenv("LLM_BACKEND", "local").lower()

    if backend == "local":
        # Local (Docker) OpenAI-compatible endpoint
        return ChatOpenAI(
            model=os.getenv("DOCKER_MODEL_NAME", "ai/gemma4"),
            base_url=os.getenv("DOCKER_MODEL_URL", "http://localhost:12434/engines/v1"),
            api_key=os.getenv("DOCKER_MODEL_API_KEY", "dummy"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
            streaming=True,
        )

    if backend == "bedrock":
        model_id = os.getenv("BEDROCK_MODEL_ID", os.getenv("BEDROCK_MODEL", "amazon.nova"))
        region = os.getenv("AWS_REGION", "us-east-1")
        return BedrockLLM(model_id=model_id, region_name=region)

    raise ValueError(f"Unsupported LLM_BACKEND: {backend}. Use 'local' or 'bedrock'.")
