from openai import OpenAI
from dotenv import load_dotenv
import json
import os

# Load from .env.local file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.local'))
client = OpenAI()

results = client.vector_stores.search(
    vector_store_id="vs_68f431dbbe7881919e3a6c420d932b3c",  # your vector store ID
    query="healthcare patient support medical terminology"  # your search query
)

print(json.dumps(results.model_dump(), indent=2))