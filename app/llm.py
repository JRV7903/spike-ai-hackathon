import os
from openai import OpenAI
from tenacity import retry, wait_exponential, stop_after_attempt

# LiteLLM is OpenAI-compatible, so we use the OpenAI SDK.

def get_llm_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("LITELLM_BASE_URL", "http://3.110.18.218")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. "
            "Make sure your .env file is loaded or environment variable is defined."
        )

    return OpenAI(
        api_key=api_key,
        base_url=base_url
    )


@retry(
    wait=wait_exponential(min=1, max=10),
    stop=stop_after_attempt(5),
)
def call_llm(messages, model="gemini-2.5-flash") -> str:
    """
    Calls LiteLLM (Gemini via OpenAI-compatible API)
    with retry + exponential backoff.
    """
    client = get_llm_client()

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0
    )

    return response.choices[0].message.content
