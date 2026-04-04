import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

DATABRICKS_HOST     = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN    = os.getenv("DATABRICKS_TOKEN")
DATABRICKS_ENDPOINT = os.getenv("DATABRICKS_ENDPOINT_NAME")

def test_connection():
    print(f"Host:     {DATABRICKS_HOST}")
    print(f"Endpoint: {DATABRICKS_ENDPOINT}")
    print(f"Token:    {DATABRICKS_TOKEN[:10]}..." if DATABRICKS_TOKEN else "Token:    NOT SET")
    print("-" * 50)

    if not all([DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_ENDPOINT]):
        print("❌ Missing env vars. Check your .env file.")
        return

    client = OpenAI(
        api_key=DATABRICKS_TOKEN,
        base_url=f"{DATABRICKS_HOST}/serving-endpoints",
    )

    print("Sending test message...")
    print("-" * 50)

    try:
        response = client.chat.completions.create(
            model=DATABRICKS_ENDPOINT,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user",   "content": "Reply with exactly: 'Databricks connection successful.'"},
            ],
            max_tokens=50,
            temperature=0,
        )

        reply = response.choices[0].message.content
        usage = response.usage

        print(f"✅ Response:      {reply}")
        print(f"   Prompt tokens: {usage.prompt_tokens}")
        print(f"   Output tokens: {usage.completion_tokens}")
        print(f"   Total tokens:  {usage.total_tokens}")
        print(f"   Model:         {response.model}")

    except Exception as e:
        print(f"❌ Connection failed: {e}")


if __name__ == "__main__":
    test_connection()