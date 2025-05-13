from llama_stack_client import LlamaStackClient
import os
from dotenv import load_dotenv

load_dotenv()

LLAMASTACK_URL = os.getenv("LLAMASTACK_URL", "http://localhost:8321")

client = LlamaStackClient(
    base_url=LLAMASTACK_URL,
)
