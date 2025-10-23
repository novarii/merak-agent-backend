from openai import OpenAI
from dotenv import load_dotenv
import json
import os

from typing import Any

# Load from .env.local file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.local'))
client = OpenAI()

results = client.vector_stores.search(
    vector_store_id="vs_68f727089ac08191824927c79f3869f6",  # your vector store ID
    query="healthcare patient support medical terminology",  # your search query
    max_num_results=1
)

def extract_agent_ids(search_results: Any) -> list[str]:
    """
    Extract agent IDs from vector store search results.
    
    Args:
        search_results: OpenAI vector store search results object
        
    Returns:
        List of agent IDs found in the search results
    """
    agent_ids = []
    
    for result in search_results.data:
        if hasattr(result, "attributes") and result.attributes:
            agent_id = result.attributes.get("agent_id")
            if agent_id:
                agent_ids.append(agent_id)
    
    return agent_ids

print(json.dumps(results.model_dump(), indent=2))
print("Extracted Agent IDs:", extract_agent_ids(results))